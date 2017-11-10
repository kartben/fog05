from dds import TopicType

class KeyValue(TopicType):
    def __init__(self, version, key, value, sid):
        self.version = version
        self.key = key
        self.value = value
        self.sid = sid

    def gen_key(self):
        return self.key


class StoreInfo(TopicType):
    def __init__(self, sid, sroot, shome):
        self.sid = sid
        self.sroot = sroot
        self.shome = shome

    def gen_key(self):
        return self.sid


class CacheMiss(TopicType):
    def __init__(self, source_sid, key):
        self.source_sid = source_sid
        self.key = key

    def gen_key(self):
       return self.key

class CacheHit(TopicType):
    def __init__(self, source_sid, dest_sid, key, value, version):
        self.source_sid = source_sid
        self.dest_sid = dest_sid
        self.key = key
        self.value = value
        self.version = version

    def gen_key(self):
       return self.key
