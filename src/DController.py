from interfaces.Store import *
from dds import *
from ddsutil import *
from utils.dutils import *
import time
import uuid
import ctypes


dds_store_info = DDSTopicInfo()
dds_store_info.idl = "/opt/fos/idl/store.idl"
dds_store_info.topic_name = "StoreInfo"
dds_store_info.type_name = "fos::dds::types::StoreInfo"
dds_store_info.key = "sid"
dds_store_info.tqos = tl_state_rqos
dds_store_info.dwqos = tl_state_wqos
dds_store_info.drqos = tl_state_rqos


dds_key_value_info = DDSTopicInfo()
dds_key_value_info.idl = "/opt/fos/idl/store.idl"
dds_key_value_info.topic_name = "KeyValue"
dds_key_value_info.type_name = "fos::dds::types::KeyValue"
dds_key_value_info.key = "key"
dds_key_value_info.tqos = cache_tl_entry_qos
dds_key_value_info.dwqos = cache_tl_entry_qos
dds_key_value_info.drqos = cache_tl_entry_qos

dds_resolve_info = DDSTopicInfo()
dds_resolve_info.idl = "/opt/fos/idl/store.idl"
dds_resolve_info.topic_name = "Resolve"
dds_resolve_info.type_name = "fos::dds::types::Resolve"
dds_resolve_info.key = "key"
dds_resolve_info.tqos = event_qos
dds_resolve_info.dwqos = event_qos
dds_resolve_info.drqos = event_qos



class DController (Controller, Observer):
    MAX_SAMPLES = 64

    def __init__(self, store):
        global dds_store_info
        global dds_key_value_info
        super(DController, self).__init__()
        self.__store = store
        dp = DomainParticipant()
        init_dds_topic_info(dp, dds_store_info)
        init_dds_topic_info(dp, dds_key_value_info)
        init_dds_topic_entities(dp, dds_store_info, [store.root])
        init_dds_topic_entities(dp, dds_key_value_info, [store.root])

        dds_store_info.listener.attachment = self
        dds_store_info.listener.actions[Action.DATA] = lambda reader, attachment: attachment.cache_discovered(reader)
        dds_store_info.listener.actions[Action.LIVELINESS_CHANGED] = lambda reader, status, attachment: attachment.cache_disappeared(reader, status)

        dds_key_value_info.listener.attachment = self
        dds_key_value_info.listener.actions[Action.DATA] = lambda reader, attachment: attachment.handle_remote_put(reader)

    # The Store Observer operations have to be updated to consider the version
    # below we also need to properly take into account the semantic of put right now
    # everything is persisted

    def handle_remote_put(self, reader):
        samples = reader.take(DController.MAX_SAMPLES)
        for (d, i) in samples:
            rkey = d.key.decode()
            rsid = d.sid.decode()
            rvalue = d.value.decode()
            rversion = d.version
            if rsid != self.__store.store_id:
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
        samples = reader.read(DController.MAX_SAMPLES, DDSMaskUtil.new_samples())
        for (d, i) in samples:
            if d is not None:
                rsid = d.sid.decode()
                print(">>> Discovered new store with id: " +  rsid)


    def cache_disappeared(self, reader, status):
        print(">>> Cache Disappeared")
        samples = reader.read(DController.MAX_SAMPLES, DDSMaskUtil.not_alive_instance_samples())
        for (d, i) in samples:
            if d is not None:
                d.print_vars()


    def onPut(self, uri, val, ver):
        global dds_key_value_info
        print(">> val: " + val)
        # dds_key_value_info.
        v = dds_key_value_info.builder(key = uri , value = val, sid = self.__store.store_id, version = ver)
        dds_key_value_info.writer.write(v)


    # One of these for each operation on the cache...
    def onPput(self, uri, val, ver):
        global dds_key_value_info

        v = dds_key_value_info.builder(key = uri , value = val, sid = self.__store.store_id, version = ver)
        dds_key_value_info.writer.write(v)

    def onDput(self, uri, val, ver):
        global dds_key_value_info

        v = dds_key_value_info.builder(key = uri , value = val, sid = self.__store.store_id, version = ver)
        dds_key_value_info.writer.write(v)


    def onGet(self, uri):
        print("onGet Not yet...")

    def onRemove(self, uri):
        print("onRemove Not yet...")

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
        global dds_store_info
        print("Starting..")

        info = dds_store_info.builder(sid = self.__store.store_id, sroot = self.__store.root, shome = self.__store.home)
        dds_store_info.writer.write(info)


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

