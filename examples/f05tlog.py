from dds import *
from fog05.interfaces.Types import *
import sys

def cache_discovered(dr):
    for (s, i) in dr.take(all_samples()):
        if i.valid_data:
            print(str(s))

def cache_disappeared():
    print("Lost one cache")

def handle_remote_put(dr):
    for (s, i) in dr.take(all_samples()):
        if i.valid_data:
            print(str(s))


def handle_miss(dr):
    for (s, i) in dr.take(all_samples()):
        if i.valid_data:
            print(str(s))


def handle_hit(dr):
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

    store_info_writer = FlexyWriter(pub,
                                         store_info_topic,
                                         [Reliable(), Transient(), KeepLastHistory(1)])

    store_info_reader = FlexyReader(sub,
                                         store_info_topic,
                                         [Reliable(), Transient(), KeepLastHistory(1)],
                                         cache_discovered)

    store_info_reader.on_liveliness_changed(cache_disappeared)

    key_value_writer = FlexyWriter(pub,
                                        key_value_topic,
                                        [Reliable(), Transient(), KeepLastHistory(1)])

    key_value_reader = FlexyReader(sub,
                                        key_value_topic,
                                        [Reliable(), Transient(), KeepLastHistory(1)],
                                        handle_remote_put)

    miss_topic = FlexyTopic(dp, "FOSStoreMiss")

    miss_writer = FlexyWriter(pub,
                                   miss_topic,
                                   [Reliable(), Volatile(), KeepAllHistory()])

    miss_reader = FlexyReader(sub,
                                   miss_topic,
                                   [Reliable(), Volatile(), KeepAllHistory()], handle_miss)

    hit_topic = FlexyTopic(dp, "FOSStoreHit")

    hit_writer = FlexyWriter(pub,
                             hit_topic,
                             [Reliable(), Volatile(), KeepAllHistory()])

    hit_reader = FlexyReader(sub,
                             hit_topic,
                             [Reliable(), Volatile(), KeepAllHistory()], handle_hit)

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
