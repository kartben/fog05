from dds import *
from ddsutil import *


# Notice that the current Python API as an issue in dealing with keep_last
v_state_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.VOLATILE),
                   ReliabilityQosPolicy(DDSReliabilityKind.BEST_EFFORT, DDSDuration.infinity())])

t_state_qos= Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT),
                  ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity())])

t_state_wqos= Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT),
                   ReliabilityQosPolicy(DDSReliabilityKind.  RELIABLE, DDSDuration.infinity()),
                   HistoryQosPolicy(DDSHistoryKind.KEEP_ALL),
                  WriterDataLifecycleQosPolicy(False)])

tl_state_wqos = Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT_LOCAL),
                     ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity()),
                     HistoryQosPolicy(DDSHistoryKind.KEEP_ALL),
                     WriterDataLifecycleQosPolicy(False)])

tl_state_rqos = Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT_LOCAL),
                     ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity())])

p_state_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.PERSISTENT),
                   ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity())])

event_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.VOLATILE),
                 ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity()),
                 HistoryQosPolicy(DDSHistoryKind.KEEP_ALL)])


cache_v_entry_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.VOLATILE),
                 ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity()),
                 HistoryQosPolicy(DDSHistoryKind.KEEP_ALL)])


cache_tl_entry_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT_LOCAL),
                 ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity()),
                 HistoryQosPolicy(DDSHistoryKind.KEEP_ALL)])

cache_t_entry_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.TRANSIENT),
                 ReliabilityQosPolicy(DDSReliabilityKind.RELIABLE, DDSDuration.infinity()),
                 HistoryQosPolicy(DDSHistoryKind.KEEP_ALL)])


cache_p_entry_qos = Qos([DurabilityQosPolicy(DDSDurabilityKind.PERSISTENT),
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
    info.listener = DataListener()

    info.writer = info.pub.create_datawriter(info.topic, info.dwqos)
    info.reader = info.sub.create_datareader(info.topic, info.drqos, info.listener)

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
    DATA_READERS = 12
    ACTION_NUM = 13

    def nothing(self, a = None, b = None, c = None, d = None, e = None):
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
    def __init__(self, attachment = None, actions = None):
        Listener.__init__(self)
        self.attachment = attachment
        if actions == None:
            self.actions = Action()
        else:
            self.actions = actions

    def on_data_available(self, reader):
        self.actions[Action.DATA](reader, self.attachment)

    def on_inconsistent_topic(self, entity, status):
        self.actions[Action.INCONSISTENT_TOPIC](entity, status, self.attachment)

    def on_liveliness_changed(self, entity, status):
        self.actions[Action.LIVELINESS_CHANGED](entity, status, self.attachment)

    def on_liveliness_lost(self, entity, status):
        self.actions[Action.LIVELINESS_LOST](entity, status, self.attachment)

    def on_data_readers(self, entity):
        self.actions[Action.DATA_READERS](entity, self.attachment)

    def on_offered_deadline_missed(self, entity, status):
        self.actions[Action.OFFERED_DEADLINE_MISSED](entity, status, self.attachment)

    def on_offered_incompatible_qos(self, entity, status):
        self.actions[Action.OFFERED_INCOMPATIBLE_QOS](entity, status, self.attachment)

    def on_publication_matched(self, entity, status):
        self.actions[Action.PUBLICATION_MATCHED](entity, status, self.attachment)

    def on_requested_deadline_missed(self, entity, status):
        self.actions[Action.REQUESTED_DEADLINE_MISSED](entity, status, self.attachment)

    def on_requested_incompatible_qos(self, entity, status):
        self.actions[Action.REQUESTED_INCOMPATIBLE_QOS](entity, status, self.attachment)

    def on_sample_lost(self, entity, status):
        self.actions[Action.SAMPLE_LOST](entity, status, self.attachment)

    def on_sample_rejected(self, entity, status):
        self.actions[Action.SAMPLE_REJECTED](entity, status, self.attachment)

    def on_subscription_matched(self, entity, status):
        self.actions[Action.SAMPLE_REJECTED](entity, status, self.attachment)




