from dds import *
from fog05.interfaces.Types import *
import sys

def cache_discovered(dr):
    for (s, i) in dr.take(all_samples()):
        if i.valid_data:
            print(str(s))

def cache_discovery_event(r, s):
    print("Cache discovery event")

def log_samples(dr):
    for (s, i) in dr.take(all_samples()):
        if i.valid_data:
            print(str(s))


def start_tlog(root):
    dds_runtime = Runtime.get_runtime()
    dp = Participant(0)
    pub = Publisher(dp, [Partition([root])])
    sub = Subscriber(dp, [Partition([root])])

    store_info_topic = FlexyTopic(dp, "FOSStoreInfo")
    key_value_topic = FlexyTopic(dp, "FOSKeyValue")

    state_qos = [Reliable(), Volatile(), KeepLastHistory(1)]
    event_qos = [Reliable(), Volatile(), KeepAllHistory()]

    store_info_writer = FlexyWriter(pub,
                                    store_info_topic,
                                    state_qos)

    store_info_reader = FlexyReader(sub,
                                    store_info_topic,
                                    state_qos,
                                    log_samples)

    store_info_reader.on_liveliness_changed(cache_discovery_event)

    key_value_writer = FlexyWriter(pub,
                                   key_value_topic,
                                   state_qos)

    key_value_reader = FlexyReader(sub,
                                   key_value_topic,
                                   state_qos,
                                   log_samples)

    miss_topic = FlexyTopic(dp, "FOSStoreMiss")

    miss_writer = FlexyWriter(pub,
                              miss_topic,
                              event_qos)

    miss_reader = FlexyReader(sub,
                              miss_topic,
                              event_qos,
                              log_samples)

    hit_topic = FlexyTopic(dp, "FOSStoreHit")

    hit_writer = FlexyWriter(pub,
                             hit_topic,
                             event_qos)

    hit_reader = FlexyReader(sub,
                             hit_topic,
                             event_qos,
                             log_samples)

    missmv_topic = FlexyTopic(dp, "FOSStoreMissMV")

    missmv_writer = FlexyWriter(pub,
                                missmv_topic,
                                event_qos)

    missmv_reader = FlexyReader(sub,
                                missmv_topic,
                                event_qos,
                                log_samples)

    hitmv_topic = FlexyTopic(dp, "FOSStoreHitMV")

    hitmv_writer = FlexyWriter(pub,
                                hitmv_topic,
                                event_qos)

    hitmv_reader = FlexyReader(sub,
                                hitmv_topic,
                                event_qos,
                               log_samples)

if __name__=='__main__':
    if len(sys.argv) > 1:
        start_tlog(sys.argv[1])
        print("Press 'x' or 'X' to exit...")
        done = False
        while done is False:
            c = input()
            if c.capitalize() == "X":
                done = True
    else:
        print("USAGE:\n\tflog")
