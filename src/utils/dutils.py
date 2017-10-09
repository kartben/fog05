from dds import *
from ddsutil import *



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



class DDSRuntime:
    pass

class DDSTopicInfo:
    pass

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

class Action(object):

    DATA = 0
    INCONSISTENT_TOPIC = 1
    LIVELINESS_CHANGED = 2
    LIVELINESS_LOST = 3
    OFFERED_DEADLINE_MISSED = 4
    REQUESTED_DEADLINE_MISSED = 5
    OFFERED_INCOMPATIBLE_QOS = 6
    REQUESTED_INCOMPATIBLE_QOS = 7
    PUBLICATION_MATCHED = 8
    SAMPLE_LOST = 9
    SAMPLE_REJECTED = 10
    SUBSCRIPTION_MATCHED = 11
    ACTION_NUM = 12

    def nothing(self):
        return

    def __init__(self):
        self.actions = {}


    def __getitem__(self, item):
        if item in self.actions:
            return self.actions[item]
        else:
            return self.nothing

    def __setitem__(self, key, value):
        self.actions[key] = value



class DataListener(Listener):
    def __init__(self, actions):
        Listener.__init__(self)
        self.actions = actions

    def on_data_available(self, reader):
        self.actions[Action.DATA](reader)




