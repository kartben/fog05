from fog05.interfaces.Store import *
from fog05.interfaces.Types import *
from fog05.DLogger import *
from dds import *
import copy

# import json

import time
import uuid
import ctypes


class DController (Controller, Observer):
    MAX_SAMPLES = 64
    DISPOSED_INSTANCE = 32

    def __init__(self, store):
        super(DController, self).__init__()
        self.logger = DLogger()
        self.__store = store

        self.dds_runtime = Runtime.get_runtime()
        self.dp = Participant(0)
        self.pub = Publisher(self.dp, [Partition([self.__store.root])])
        self.sub = Subscriber(self.dp, [Partition([self.__store.root])])

        self.store_info_topic = FlexyTopic(self.dp, "FOSStoreInfo")
        self.key_value_topic = FlexyTopic(self.dp, "FOSKeyValue")

        self.hit_topic = FlexyTopic(self.dp, "FOSStoreHit")
        self.miss_topic = FlexyTopic(self.dp, "FOSStoreMiss")

        self.missmv_topic = FlexyTopic(self.dp, "FOSStoreMissMV")
        self.hitmv_topic = FlexyTopic(self.dp, "FOSStoreHitMV")

        state_qos = [Reliable(), TransientLocal(), KeepLastHistory(1), ManualInstanceDispose()]
        event_qos = [Reliable(), Volatile(), KeepAllHistory()]

        self.store_info_writer = FlexyWriter(self.pub,
                                             self.store_info_topic,
                                            state_qos)

        self.store_info_reader = FlexyReader(self.sub,
                                            self.store_info_topic,
                                             state_qos,
                                            self.cache_discovered)


        self.store_info_reader.on_liveliness_changed(self.cache_disappeared)

        self.key_value_writer = FlexyWriter(self.pub,
                                            self.key_value_topic,
                                            state_qos)

        self.key_value_reader = FlexyReader(self.sub,
                                            self.key_value_topic,
                                            state_qos,
                                            self.handle_remote_put)


        self.miss_writer = FlexyWriter(self.pub,
                                       self.miss_topic,
                                       event_qos)

        self.miss_reader = FlexyReader(self.sub,
                                       self.miss_topic,
                                       event_qos, self.handle_miss)


        self.hit_writer = FlexyWriter(self.pub,
                                       self.hit_topic,
                                       event_qos)

        self.hit_reader = FlexyReader(self.sub,
                                       self.hit_topic,
                                       event_qos,
                                      None)

        # self.hit_log_reader = FlexyReader(self.sub,
        #                                   self.hit_topic,
        #                                   event_qos,
        #                                   self.log_samples)

        self.missmv_writer = FlexyWriter(self.pub,
                                         self.missmv_topic,
                                         event_qos)

        self.missmv_reader = FlexyReader(self.sub,
                                         self.missmv_topic,
                                         event_qos, lambda r: self.handle_miss_mv(r))



        self.hitmv_writer = FlexyWriter(self.pub,
                                        self.hitmv_topic,
                                        event_qos)


        self.hitmv_reader = FlexyReader(self.sub,
                                        self.hitmv_topic,
                                        event_qos, None)

        # self.hitmv_log_reader = FlexyReader(self.sub,
        #                                   self.hitmv_topic,
        #                                   event_qos,
        #                                   self.log_samples)

    def log_samples(self, dr):
        for (s, i) in dr.read(all_samples()):
            if i.valid_data:
                print(str(s))

    def handle_miss(self, r):
        print('DController.handle_miss','Handling Miss for store {0}'.format(self.__store.store_id))
        samples = r.take(all_samples())
        for (d, i) in samples:
            if i.valid_data and (d.source_sid != self.__store.store_id):
                v = self.__store.get_value(d.key)
                if v is not None:
                    print('DController.handle_miss', 'Serving Miss for {0}'.format(d.key))
                    h = CacheHit(self.__store.store_id, d.source_sid, d.key, v[0], v[1])
                    self.hit_writer.write(h)
                else:
                    print('DController.handle_miss', 'Store {0} did not resolve remote miss on key {1}'.format(self.__store.store_id, d.key))


    def handle_miss_mv(self, r):
        print('>>>> Handling Miss MV for store {0}'.format(self.__store.store_id))
        samples = r.take(all_samples())
        for (d, i) in samples:
            if i.valid_data and (d.source_sid != self.__store.store_id):
                xs = self.__store.getAll(d.key)
                print('>>>> Serving Miss MV for key {0}'.format(d.key))
                h = CacheHitMV(self.__store.store_id, d.source_sid, d.key, xs)
                self.hitmv_writer.write(h)


    def handle_remove(self, uri):
        print('>>>> Removing {0}'.format(uri))
        self.__store.remote_remove(uri)

    def handle_remote_put(self, reader):
        samples = reader.take(DDS_NOT_READ_SAMPLE_STATE)
        for (d, i) in samples:
            if i.is_disposed_instance():
                self.handle_remove(d.key)
            elif i.valid_data:
                rkey = d.key
                rsid = d.sid
                rvalue = d.value
                rversion = d.version
                if rsid != self.__store.store_id and rkey.startswith(self.__store.home):
                    print(">>>>>>>> Handling remote put for key = " + rkey)
                    r = self.__store.update_value(rkey, rvalue, rversion)
                    if r:
                        print(">> Updated " + rkey)
                        self.__store.notify_observers(rkey, rvalue, rversion)
                    else:
                        print(">> Received old version of " + rkey)
                else:
                    if rsid != self.__store.store_id and self.__store.get_value(rkey) is not None:
                        r = self.__store.update_value(rkey, rvalue, rversion)
                        if r:
                            print(">> Updated " + rkey)
                            self.__store.notify_observers(rkey, rvalue, rversion)
                        else:
                            print(">> Received old version of " + rkey)
                    else:
                        print(">>>>>> Ignoring remote put as it is a self-put")
            else:
                print(">>>>>> Some store unregistered instance {0}".format(d.key))



    def cache_discovered(self,reader):
        print('New Cache discovered, current view = {0}'.format(self.__store.discovered_stores))
        samples = reader.take(DDS_NOT_READ_SAMPLE_STATE)

        for (d, i) in samples:
            if i.valid_data:
                rsid = d.sid
                print(">>> Discovered new store with id: " + rsid)
                if rsid != self.__store.store_id and not rsid in self.__store.discovered_stores:
                    self.__store.discovered_stores.append(rsid)
                    self.advertise_presence()



    def cache_disappeared(self, reader, status):
        print(">>> Cache Lifecycle-Change")
        print('Current Stores view = {0}'.format(self.__store.discovered_stores))
        samples = reader.take(DDS_NOT_ALIVE_NO_WRITERS_INSTANCE_STATE | DDS_NOT_ALIVE_DISPOSED_INSTANCE_STATE)
        for (d, i) in samples:
            if i.valid_data:
                rsid = d.sid
                if rsid != self.__store.store_id:
                    if rsid in self.__store.discovered_stores:
                        self.__store.discovered_stores.remove(rsid)
                        print(">>> Store with id {0} has disappeared".format(rsid))
                    else:
                        print(">>> Store with id {0} has disappeared, but for some reason we did not know it...")


    def onPut(self, uri, val, ver):
        # print(">> uri: " + uri)
        # print(">> val: " + val)
        v = KeyValue(key = uri , value = val, sid = self.__store.store_id, version = ver)
        self.key_value_writer.write(v)


    # One of these for each operation on the cache...
    def onPput(self, uri, val, ver):
        v = KeyValue(key = uri , value = val, sid = self.__store.store_id, version = ver)
        self.key_value_writer.write(v)

    def onDput(self, uri, val, ver):
        v = KeyValue(key = uri , value = val, sid = self.__store.store_id, version = ver)
        self.key_value_writer.write(v)


    def onGet(self, uri):
        pass
        # print("onGet Not yet...")

    def onRemove(self, uri):
        v = KeyValue(key=uri, value=uri, sid=self.__store.store_id, version=0)
        self.key_value_writer.dispose_instance(v)


    def onObserve(self, uri, action):
        pass
        # print("onObserve Not yet...")

    def onMiss(self):
        pass
        # print(">> onMiss")

    def onConflict(self):
        pass
        # print("onConflict Not yet...")

    def resolveAll(self, uri, timeout = None):
        print('>>>> Handling {0} Miss MV for store {1}'.format(uri, self.__store.store_id))

        print(">> Trying to resolve %s" % uri)
        """
            Tries to resolve this URI (with wildcards) across the distributed caches
            :param uri: the URI to be resolved
            :return: the [value], if something is found
        """
        # @TODO: This should be in the config...

        delta = 0.250
        if timeout is None:
            timeout = delta

        m = CacheMissMV(self.__store.store_id, uri)
        self.missmv_writer.write(m)

        peers = copy.deepcopy(self.__store.discovered_stores)
        maxRetries = max(len(peers),  3)
        retries = 0
        values = []
        while (peers != [] and retries < maxRetries):
            samples = self.hitmv_reader.take(DDS_ANY_STATE)
            time.sleep(timeout + max(retries - 1, 0) * delta)
            print(">>>> Resolve loop #{0} got {1} samples".format(retries, str(samples)))
            for s in samples:
                d = s[0]
                i = s[1]
                # print("Is valid data: {0}".format(i.valid_data))
                # print("Key: {0}".format(d.key))
                if i.valid_data:
                    # print("Reveived data from store {0} for store {1} on key {2}".format(d.source_sid, d.dest_sid, d.key))
                    # print("I was looking to resolve uri: {0}".format(uri))
                    # print('>>>>>>>>> VALUE {0} KVAVE {1}'.format(values, d.kvave))
                    # Only remove if this was an answer for this key!
                    if d.source_sid in peers and uri == d.key:
                        peers.remove(d.source_sid)
                    if d.key == uri: # and d.dest_sid == self.__store.store_id:
                        values = values + d.kvave


            retries += 1

        # now we need to consolidate values
        # print("Resolved Values = {0}".format(values))
        filtered_values = []
        for (k,va,ve) in values:
            key = k
            value = va
            version = ve
            for (a,b,c) in values:
                if a == key and version < c:
                    key = a
                    value = b
                    version = c
            filtered_values.append((key, value, version))

        # print("Filtered Values = {0}".format(filtered_values))
        return filtered_values

    def resolve(self, uri, timeout = None):
        print('>>>> Handling {0} Miss for store {1}'.format(uri, self.__store.store_id))

        print(">> Trying to resolve %s" % uri)
        """
            Tries to resolve this URI on across the distributed caches
            :param uri: the URI to be resolved
            :return: the value, if something is found
        """
        # @TODO: This should be in the config...
        delta = 0.250
        if timeout is None:
            timeout = delta


        m = CacheMiss(self.__store.store_id, uri)
        self.miss_writer.write(m)

        peers = copy.deepcopy(self.__store.discovered_stores)
        # print("Trying to resolve {0} with peers {1}".format(uri, peers))
        maxRetries = max(len(peers),  3)

        retries = 0
        v = (None, -1)
        while peers != [] and retries < maxRetries:
            samples = self.hit_reader.take(DDS_ANY_STATE)
            time.sleep(timeout + max(retries-1, 0) * delta)
            # print(">>>> Resolve loop #{0} got {1}".format(retries, str(samples)))

            sn = 0
            for (d, i) in samples:
                sn += 1
                if i.valid_data and d.key == uri:
                    # print("Reveived data from store {0} for store {1} on key {2}".format(d.source_sid, d.dest_sid, d.key))
                    # print("I was looking to resolve uri: {0}".format(uri))
                    # # Only remove if this was an answer for this key!
                    if d.source_sid in peers and uri == d.key and d.dest_sid == self.__store.store_id:
                        peers.remove(d.source_sid)

                    if d.key == uri and d.dest_sid == self.__store.store_id:
                        if int(d.version) > int(v[1]):
                            v = (d.value, d.version)


            if sn == 0 and v[0] is not None:
                return v

            retries += 1

        return v


    def start(self):
        print("Advertising Store with Id {0}".format(self.__store.store_id))
        self.advertise_presence()

    def advertise_presence(self):
        info = StoreInfo(sid=self.__store.store_id, sroot=self.__store.root, shome=self.__store.home)
        self.store_info_writer.write(info)

    def pause(self):
        """
            Pauses the execution of the controller. The incoming updates are not lost.
        """
        pass
        # print("Pausing..")


    def resume(self):
        """
            Resumes the execution of the controller and applies all pending changes received from the network.
        """
        pass
        # print("Resuming..")


    def stop(self):
        """
            Stops a controller and releases all resources used to receive/send data on the network.
        """
        pass
        # print("Stopping..")

