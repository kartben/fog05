from interfaces.Store import *
from dds import *
from ddsutil import *
import time
import uuid

class DDSRuntime:
    pass


class DDSTopicInfo:
    pass


# Notice that the current Python API as an issue in dealing with keep_last
v_state_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.VOLATILE),
                   ReliabilityQosPolicy(DDSReliabilityKind.BEST_EFFORT, DDSDuration.infinity())])

t_state_qos= Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT),
                  ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity())])

t_state_wqos= Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT),
                   ReliabilityQosPolicy(DDSReliabilityKind.  RELIABLE, DDSDuration.infinity()),
                   HistoryQosPolicy(DDSHistoryKind.KEEP_ALL)])

tl_state_wqos = Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT_LOCAL),
                     ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity()),
                     HistoryQosPolicy(DDSHistoryKind.KEEP_ALL)])

tl_state_rqos = Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT_LOCAL),
                     ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity())])

p_state_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.PERSISTENT),
                   ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity())])

event_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.VOLATILE),
                 ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity()),
                 HistoryQosPolicy(DDSHistoryKind.KEEP_ALL)])



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
dds_key_value_info.tqos = t_state_qos
dds_key_value_info.dwqos = t_state_wqos
dds_key_value_info.drqos = t_state_qos

dds_resolve_info = DDSTopicInfo()
dds_resolve_info.idl = "/opt/fos/idl/store.idl"
dds_resolve_info.topic_name = "Resolve"
dds_resolve_info.type_name = "fos::dds::types::Resolve"
dds_resolve_info.key = "key"
dds_resolve_info.tqos = event_qos
dds_resolve_info.dwqos = event_qos
dds_resolve_info.drqos = event_qos



def init_dds_topic_info(dp, info):
    # Using the path ~/.fos/src/dds/idl/store.idl does not seem to be liked by this function...
    info.type = get_dds_classes_from_idl(info.idl, info.type_name, info.key)

    # Once the problem with the QoS settings is fixed we should use a qos attribute in the info class to store
    # the qos for the topic
    info.topic = info.type.register_topic(dp, info.topic_name, tl_state_rqos)

    info.builder = info.type.get_class(info.type_name)

# The info should  be properly initialised
def init_dds_topic_entities(dp, info, partitions):

    ps_qos = Qos([PresentationQosPolicy(DDSPresentationAccessScopeKind.TOPIC, True, True),
                PartitionQosPolicy(partitions)])

    info.pub = dp.create_publisher(ps_qos)
    info.sub = dp.create_subscriber(ps_qos)

    # store_info_writer = pub.create_datawriter(store_info_topic, writer_qos)
    info.writer = info.pub.create_datawriter(info.topic, info.dwqos)
    info.reader = info.sub.create_datareader(info.topic, info.drqos)



def run_store_info():
    global dds_store_info

    store_info_builder = dds_store_info.type.get_class("fos::dds::types::StoreInfo")
    root = "fos://system0"
    home = root + "/node0"
    store = "store0"
    info = store_info_builder(store_id = store, sroot = root, shome = home)
    dds_store_info.writer.write(info)

    sid = str(uuid.uuid4())

    v = 1
    k = 0
    while True:
        key_value_builder = dds_key_value_info.type.get_class(dds_key_value_info.type_name)
        kv = key_value_builder(uri = "fos://system0/node0/plugins" + str(k) , value="{\"name\": \"foo\"}", store_id = sid, revision = v)
        print(">> " + str(kv))
        dds_key_value_info.writer.write(kv)
        time.sleep(5)
        v = v + 1
        k = k + 1


def run_store_info_logger():
    global dds_store_info
    while (True):
        samples = dds_store_info.reader.take()
        for d, i in samples:
            d.print_vars()

        kvs = dds_key_value_info.reader.read()
        for kv, i in kvs:
            kv.print_vars()

        time.sleep(5)



class DController (Controller, Observer):

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

    # The Store Observer operations have to be updated to consider the version
    # below we also need to properly take into account the semantic of put right now
    # everything is persisted

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
        """
            This method starts the controller and "connects" the cache to the rest of the system.

        """
        print("Starting..")

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

