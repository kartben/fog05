

class Agent():

    def loadOSPlugin(self):
        raise NotImplementedError

    def loadRuntimePlugin(self,plugin_name):
        raise NotImplementedError

    def refreshPlugins(self):
        raise NotImplementedError

    def loadNetworkPlugin(self,plugin_name):
        raise NotImplementedError

    def getOSPlugin(self):
        raise NotImplementedError

    def getRuntimePlugin(self,runtime_name):
        raise NotImplementedError

    def getNetworkPlugin(self,network_name):
        raise NotImplementedError

    def listRuntimePlugins(self):
        raise NotImplementedError
    
    def listNetworkPlugins(self):
        raise NotImplementedError

