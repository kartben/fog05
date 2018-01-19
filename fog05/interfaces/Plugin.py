import uuid

class Plugin(object):

    def __init__(self, version, plugin_uuid=None):
        self.version = version
        if uuid is None:
            self.uuid = uuid.uuid4()
        else:
            self.uuid = plugin_uuid

    def get_version(self):
        return self.version

    def react_to_cache(self, key, value, version):
        raise NotImplemented