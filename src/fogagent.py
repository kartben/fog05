from interfaces import Agent
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



    def loadOSPlugin(self):
        platform = sys.platform
        if platform == 'linux':
            print("I'am on Linux")
        elif platform == 'darwin':
            print("I'am on Mac")
        elif platform == 'windows':
            print("I'am on Windows")
        else:
            raise RuntimeError("Platform not compatible")


    def loadRuntimePlugin(self,plugin_name):
        rt = self.pl.locatePlugin(plugin_name)
        if rt != None:
            rt = self.pl.loadPlugin(rt)
            rt = rt.run()
            return rt
        else:
            return None
    
    def main(self):
        
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






if __name__=='__main__':
    FogAgent().main()

