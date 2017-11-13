import uuid

class Plugin(object):

    def __init__(self,version):
        self.version=version
        self.uuid = uuid.uuid4()

    def getVersion(self):
        return self.version

    def reactToCache(self, key, value):
        raise NotImplemented