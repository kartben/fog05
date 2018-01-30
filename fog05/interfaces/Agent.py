class Agent(object):

    def __init__(self, uuid):
        self.uuid = uuid

    def __load_os_plugin(self):
        raise NotImplementedError

    def __load_runtime_plugin(self, plugin_name, plugin_uuid):
        raise NotImplementedError

    def refresh_plugins(self):
        raise NotImplementedError

    def __load_network_plugin(self, plugin_name, plugin_uuid):
        raise NotImplementedError

    def __load_monitoring_plugin(self, plugin_name, plugin_uuid):
        raise NotImplementedError

    def get_os_plugin(self):
        raise NotImplementedError

    def get_runtime_plugin(self, runtime_uuid):
        raise NotImplementedError

    def get_network_plugin(self, cnetwork_uuid):
        raise NotImplementedError

    def list_runtime_plugins(self):
        raise NotImplementedError
    
    def list_network_plugins(self):
        raise NotImplementedError

