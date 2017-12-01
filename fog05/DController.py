from fog05.interfaces.Store import *
from fog05.interfaces.Types import *
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
        self.__store = store

        self.dds_runtime = Runtime.get_runtime()
        self.dp = Participant(0)
        self.pub = Publisher(self.dp, [Partition([self.__store.root])])
        self.sub = Subscriber(self.dp, [Partition([self.__store.root])])

        self.store_info_topic = FlexyTopic(self.dp, "FOSStoreInfo")
        self.key_value_topic = FlexyTopic(self.dp, "FOSKeyValue")


        self.store_info_writer = FlexyWriter(self.pub,
                                             self.store_info_topic,
                                            [Reliable(), Transient(), KeepLastHistory(1)])

        self.store_info_reader = FlexyReader(self.sub,
                                            self.store_info_topic,
                                            [Reliable(), Transient(), KeepLastHistory(1)],
                                            self.cache_discovered)


        self.store_info_reader.on_liveliness_changed(self.cache_disappeared)

        self.key_value_writer = FlexyWriter(self.pub,
                                            self.key_value_topic,
                                            [Reliable(), Transient(), KeepLastHistory(1)])

        self.key_value_reader = FlexyReader(self.sub,
                                            self.key_value_topic,
                                            [Reliable(), Transient(), KeepLastHistory(1)],
                                            lambda r: self.handle_remote_put(r))


        self.miss_topic = FlexyTopic(self.dp, "FOSStoreMiss")


        self.miss_writer = FlexyWriter(self.pub,
                                       self.miss_topic,
                                       [Reliable(), Volatile(), KeepAllHistory()])

        self.miss_reader = FlexyReader(self.sub,
                                       self.miss_topic,
                                       [Reliable(), Volatile(), KeepAllHistory()], lambda r: self.handle_miss(r))

        self.hit_topic = FlexyTopic(self.dp, "FOSStoreHit")

        self.hit_writer = FlexyWriter(self.pub,
                                       self.hit_topic,
                                       [Reliable(), Volatile(), KeepAllHistory()])

        self.hit_reader = FlexyReader(self.sub,
                                       self.hit_topic,
                                       [Reliable(), Volatile(), KeepAllHistory()], None)

        self.missmv_topic = FlexyTopic(self.dp, "FOSStoreMissMV")

        self.missmv_writer = FlexyWriter(self.pub,
                                         self.missmv_topic,
                                         [Reliable(), Volatile(), KeepAllHistory()])

        self.missmv_reader = FlexyReader(self.sub,
                                         self.missmv_topic,
                                         [Reliable(), Volatile(), KeepAllHistory()], lambda r: self.handle_miss_mv(r))

        self.hitmv_topic = FlexyTopic(self.dp, "FOSStoreHitMV")

        self.hitmv_writer = FlexyWriter(self.pub,
                                        self.hitmv_topic,
                                        [Reliable(), Volatile(), KeepAllHistory()])

        self.hitmv_reader = FlexyReader(self.sub,
                                        self.hitmv_topic,
                                        [Reliable(), Volatile(), KeepAllHistory()], None)


    def handle_miss(self, r):
        print('>>>> Handling Miss for store {0}'.format(self.__store.store_id))
        samples = r.take(all_samples())
        for (d, i) in samples:
            if i.valid_data and (d.source_sid != self.__store.store_id):
                v = self.__store.get_value(d.key)
                if v is not None:
                    print('>>>> Serving Miss')
                    h = CacheHit(self.__store.store_id, d.source_sid, d.key, v, self.__store.get_version(d.key))
                    self.hit_writer.write(h)
                else:
                    print(">>> Store {0} not resolve remote miss on key {1}".format(self.__store.store_id, d.key))


    def handle_miss_mv(self, r):
        print('>>>> Handling Miss MV for store {0}'.format(self.__store.store_id))
        samples = r.take(all_samples())
        for (d, i) in samples:
            if i.valid_data and (d.source_sid != self.__store.store_id):
                xs = self.__store.getAll(d.key)
                print('>>>> Serving Miss')
                h = CacheHitMV(self.__store.store_id, d.source_sid, d.key, xs)
                self.hit_writer.write(h)


    def handle_remove(self, uri):
        self.__store.remote_remove(uri)

    def handle_remote_put(self, reader):
        samples = reader.take(DDS_NOT_READ_SAMPLE_STATE)
        for (d, i) in samples:
            if i.is_disposed_instance():
                self.handle_remove(d.key)
            else:
                rkey = d.key
                rsid = d.sid
                rvalue = d.value
                rversion = d.version
                if rsid != self.__store.store_id and rkey.startswith(self.__store.root):
                    print(">>>>>>>> Handling remote put for key = " + rkey)
                    r = self.__store.update_value(rkey, rvalue, rversion)
                    if r:
                        print(">> Updated " + rkey)
                        self.__store.notify_observers(rkey, rvalue, rversion)
                    else:
                        print(">> Received old version of " + rkey)
                else:
                    print(">>>>>> Ignoring remote put as it is a self-put")



    def cache_discovered(self,reader):
        samples = reader.read(DDS_NOT_READ_SAMPLE_STATE)
        for (d, i) in samples:
            if i.valid_data:
                rsid = d.sid
                if rsid != self.__store.store_id:
                    self.__store.discovered_stores.append(rsid)
                    print(">>> Discovered new store with id: " +  rsid)



    def cache_disappeared(self, reader, status):
        print(">>> Cache Disappeared")
        samples = reader.read(DDS_NOT_ALIVE_NO_WRITERS_INSTANCE_STATE | DDS_NOT_ALIVE_DISPOSED_INSTANCE_STATE)
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
        print(">> uri: " + uri)
        print(">> val: " + val)
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
        print("onGet Not yet...")

    def onRemove(self, uri):
        v = KeyValue(key=uri, value=uri, sid=self.__store.store_id, version=0)
        self.key_value_writer.dispose_instance(v)


    def onObserve(self, uri, action):
        print("onObserve Not yet...")

    def onMiss(self):
        print(">> onMiss")

    def onConflict(self):
        print("onConflict Not yet...")

    def resolveAll(self, uri, timeout = None):
        print('>>>> Handling {0} Miss MV for store {1}'.format(uri, self.__store.store_id))

        print(">> Trying to resolve %s" % uri)
        """
            Tries to resolve this URI (with wildcards) across the distributed caches
            :param uri: the URI to be resolved
            :return: the [value], if something is found
        """
        # @TODO: This should be in the config...

        if timeout is None:
            timeout = dds_secs(1)

        m = CacheMissMV(self.__store.store_id, uri)
        self.missmv_writer.write(m)

        peers = copy.deepcopy(self.__store.discovered_stores)
        maxRetries = len(peers)
        retries = 0
        values = []
        while (peers != [] and retries < maxRetries):
            samples = self.hitmv_reader.stake(new_samples(), timeout)

            for (d, i) in samples:
                if d.source_sid in peers:
                    peers.remove(d.source_sid)

                if i.valid_data:
                    print("Reveived data from store {0} for store {1} on key {2}".format(d.source_sid, d.dest_sid, d.key))
                    print("I was looking to resolve uri: {0}".format(uri))
                    # source_sid, dest_sid, key, kvave):
                    if d.key == uri and d.dest_sid == self.__store.store_id:
                        values = values + d.kvave

                retries += 1

        # now we need to consolidate values

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
            filtered_values.append((version, value, key))

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
        if timeout is None:
            timeout = dds_secs(3)

        m = CacheMiss(self.__store.store_id, uri)
        self.miss_writer.write(m)
        samples = self.hit_reader.stake(new_samples(), timeout)

        for (d, i) in samples:
            if i.valid_data:
                print("Reveived data from store {0} for store {1} on key {2}".format(d.source_sid, d.dest_sid, d.key))
                print("I was looking to resolve uri: {0}".format(uri))
                if d.key == uri and d.dest_sid == self.__store.store_id:
                    return (d.value, d.version)

        return None


    def start(self):
        print("Advertising Store with Id {0}".format(self.__store.store_id))
        info = StoreInfo(sid = self.__store.store_id, sroot = self.__store.root, shome = self.__store.home)
        self.store_info_writer.write(info)


    def pause(self):
        """
            Pauses the execution of the controller. The incoming updates are not lost.
        """
        print("Pausing..")


    def resume(self):
        """
            Resumes the execution of the controller and applies all pending changes received from the network.
        """
        print("Resuming..")


    def stop(self):
        """
            Stops a controller and releases all resources used to receive/send data on the network.
        """
        print("Stopping..")

