class Agent(object):

    def __init__(self, uuid):
        self.uuid = uuid

    def __load_os_plugin(self):
        raise NotImplementedError

    def __load_runtime_plugin(self, plugin_name, plugin_uuid):
        raise NotImplementedError

    def refreshPlugins(self):
        raise NotImplementedError

    def __load_network_plugin(self, plugin_name, plugin_uuid):
        raise NotImplementedError

    def __load_monitoring_plugin(self, plugin_name, plugin_uuid):
        raise NotImplementedError

    def getOSPlugin(self):
        raise NotImplementedError

    def getRuntimePlugin(self, runtime_uuid):
        raise NotImplementedError

    def getNetworkPlugin(self, cnetwork_uuid):
        raise NotImplementedError

    def listRuntimePlugins(self):
        raise NotImplementedError
    
    def listNetworkPlugins(self):
        raise NotImplementedError

