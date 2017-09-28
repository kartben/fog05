from interfaces.Agent import Agent
from PluginLoader import PluginLoader
import uuid
import sys


class FogAgent(Agent):

    def __init__(self):
        self.PLUINGDIR='./plugins'
        self.pl=PluginLoader(self.PLUINGDIR)
        self.pl.getPlugins()
        self.osPlugin=None
        self.rtPlugins={}
        self.nwPlugins={}
        self.loadOSPlugin()
        super(FogAgent, self).__init__(uuid.uuid4())



    def loadOSPlugin(self):
        platform = sys.platform
        if platform == 'linux':
            print("I'am on Linux")
            os = self.pl.locatePlugin('linux')
            if os != None:
                os = self.pl.loadPlugin(os)
                self.osPlugin = os.run()
            else:
                raise RuntimeError("Error on loading OS Plugin")
        elif platform == 'darwin':
            print("I'am on Mac")
        elif platform == 'windows':
            print("I'am on Windows")
        else:
            raise RuntimeError("Platform not compatible")

    def getOSPlugin(self):
        return self.osPlugin


    def loadRuntimePlugin(self,plugin_name):
        rt = self.pl.locatePlugin(plugin_name)
        if rt != None:
            rt = self.pl.loadPlugin(rt)
            rt = rt.run()
            self.rtPlugins.update({rt.uuid:rt})
            return rt
        else:
            return None
    
    def main(self):
        

        self.osPlugin.executeCommand("ls -al /")
        '''
        kvm = self.loadRuntimePlugin('RuntimeLibVirt')
        if kvm != None:
            print("KVM Runtime UUID: %s\n" % kvm.startRuntime())
            test_uuid=kvm.defineEntity('test',512,1,5)
            print("test vm uuid %s\n" % test_uuid)
            print("entities inside kvm " )
            print(kvm.getEntities)
            print("Result of configuring %s is %s" % (test_uuid,kvm.configureEntity(test_uuid)))
        else:
            print("Error on plugin load")

        print (self.rtPlugins)
        '''





if __name__=='__main__':
    agent = FogAgent()
    agent.main()

