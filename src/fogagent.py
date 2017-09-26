from PluginLoader import PluginLoader
import uuid


class FogAgent():
    def __init__(self):
        self.PLUINGDIR='./plugins'
    
    def main(self):
        pl = PluginLoader("./plugins")
        pl.getPlugins()
        kvm=pl.locatePlugin('RuntimeLibVirt')
        if kvm != None:
            kvm=pl.loadPlugin(kvm)
            kvm = kvm.run()
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

