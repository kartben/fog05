from fog05.interfaces.Store import *
from fog05.interfaces.Types import *
from dds import *

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
        self.pub = Publisher(self.dp, [Partition(["fos://store$"])])
        self.sub = Subscriber(self.dp, [Partition(["fos://store$"])])

        self.store_info_topic = FlexyTopic(self.dp, "FOSStoreInfo")
        self.key_value_topic = FlexyTopic(self.dp, "FOSKeyValue")


        self.store_info_writer = FlexyWriter(self.pub,
                                             self.store_info_topic,
                                            [Reliable(), TransientLocal(), KeepLastHistory(1)])

        self.store_info_reader = FlexyReader(self.sub,
                                            self.store_info_topic,
                                            [Reliable(), TransientLocal(), KeepLastHistory(1)],
                                            self.cache_discovered)


        self.store_info_reader.on_liveliness_changed(self.cache_disappeared)

        self.key_value_writer = FlexyWriter(self.pub,
                                            self.key_value_topic,
                                            [Reliable(), TransientLocal(), KeepLastHistory(1)])

        self.key_value_reader = FlexyReader(self.sub,
                                            self.key_value_topic,
                                            [Reliable(), TransientLocal(), KeepLastHistory(1)],
                                            lambda r: self.handle_remote_put(r))





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
                print(">>> Discovered new store with id: " +  rsid)



    def cache_disappeared(self, reader, status):
        print(">>> Cache Disappeared")
        samples = reader.read(DDS_NOT_ALIVE_NO_WRITERS_INSTANCE_STATE | DDS_NOT_ALIVE_DISPOSED_INSTANCE_STATE)
        for (d, i) in samples:
            if d is not None:
                d.print_vars()


    def onPut(self, uri, val, ver):
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
        print("onMiss Not yet...")

    def onConflict(self):
        print("onConflict Not yet...")


    def resolve(self, uri):
        """
            Tries to resolve this URI on across the distributed caches
            :param uri: the URI to be resolved
            :return: the value, if something is found
        """
        print("Resolving...")
        return None

    def start(self):
        print("Advertising Store..")
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

