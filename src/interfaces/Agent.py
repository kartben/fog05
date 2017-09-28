class Agent(object):

    def __init__(self,uuid):
        self.uuid = uuid

    def loadOSPlugin(self):
        raise NotImplementedError

    def loadRuntimePlugin(self, plugin_name):
        raise NotImplementedError

    def refreshPlugins(self):
        raise NotImplementedError

    def loadNetworkPlugin(self, plugin_name):
        raise NotImplementedError

    def getOSPlugin(self):
        raise NotImplementedError

    def getRuntimePlugin(self, runtime_uuid):
        raise NotImplementedError

    def getNetworkPlugin(self,cnetwork_uuid):
        raise NotImplementedError

    def listRuntimePlugins(self):
        raise NotImplementedError
    
    def listNetworkPlugins(self):
        raise NotImplementedError

