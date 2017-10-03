from interfaces.Agent import Agent
from PluginLoader import PluginLoader
import uuid
import sys
from DDSCache import *
import json

class FogAgent(Agent):

    def __init__(self):
        self.PLUINGDIR ='./plugins'
        self.pl=PluginLoader(self.PLUINGDIR)
        self.pl.getPlugins()
        self.osPlugin = None
        self.rtPlugins = {}
        self.nwPlugins = {}
        self.loadOSPlugin()
        super(FogAgent, self).__init__(self.osPlugin.getUUID())
        self.cache = DDSCache(10, self.uuid,DDSObserver())

        val = {'status': 'add', 'version': self.osPlugin.version, 'description': 'linux plugin'}
        uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, self.osPlugin.name, self.osPlugin.uuid))
        self.cache.put(uri, self.osPlugin)


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

    def loadRuntimePlugin(self, plugin_name):
        rt = self.pl.locatePlugin(plugin_name)
        if rt is not None:
            rt = self.pl.loadPlugin(rt)
            rt = rt.run(agent=self)
            self.rtPlugins.update({rt.uuid: rt})

            val = {'status': 'add', 'version': rt.version, 'description':str('runtime %s'  % rt.name)}
            uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, rt.name, rt.uuid))
            self.cache.put(uri, rt)
            return rt
        else:
            return None
    
    def main(self):

        print(self.cache)

        kvm = self.loadRuntimePlugin('RuntimeLibVirt')

        print (self.cache)


        d = self.cache.get(str('fos://*/%s/plugins/kvm-libvirt' % self.uuid))
        for a in d:
            kvm = a[list(a.keys())[0]]
            kvm_uuid = kvm.startRuntime()
            uri = str('fos://<sys-id>/%s/runtime/%s' % (self.uuid, kvm_uuid))
            self.cache.put(uri, kvm)

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/*' % (self.uuid, kvm_uuid))
        self.cache.observe(uri,kvm.reactToCache)

        print("Press enter to define a vm")
        input()

        vm_uuid = str(uuid.uuid4())
        vm_name = 'test'

        vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 512, 'disk_size': 5, 'base_image':
            'cirros-0.3.5-x86_64-disk.img' }

        entity_definition = {'status': 'define', 'name': vm_name, 'version': 1, 'entity_data': vm_definition}

        json_data = json.dumps(entity_definition)
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, kvm_uuid, vm_uuid))
        self.cache.put(uri, json_data)
        print (self.cache)

        print (kvm.getEntities())


        print("Press enter to configure the vm")
        input()

        #json_data = json.dumps({'status': 'configure'})
        #uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, kvm_uuid, vm_uuid))
        #self.cache.put(uri, json_data)
        #print (self.cache)


        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (self.uuid, kvm_uuid, vm_uuid))
        self.cache.dput(uri)
        print (self.cache)

        print("Press enter to start vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (self.uuid, kvm_uuid, vm_uuid))
        self.cache.dput(uri)
        print (self.cache)

        print("Press enter to stop vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' % (self.uuid, kvm_uuid, vm_uuid))
        self.cache.dput(uri)
        print (self.cache)

        print("Press enter to clean vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' % (self.uuid, kvm_uuid, vm_uuid))
        self.cache.dput(uri)
        print (self.cache)
        print("Press enter to undefine vm")
        input()

        json_data = json.dumps({'status': 'undefine'})
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, kvm_uuid, vm_uuid))
        self.cache.put(uri, json_data)
        print (self.cache)

        '''

        data = self.cache.get(str('fos://*/%s/runtime/%s' % (self.uuid, kvm_uuid)))
        for a in d:
            kvm = a[list(a.keys())[0]]
            test_uuid = kvm.defineEntity('test', 512, 1, 5,uuid.uuid4(),'cirros.img')
            uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, kvm_uuid, test_uuid))
            self.cache.put(uri, "")

            print (self.cache)

            print("test vm uuid %s\n" % test_uuid)
            print("entities inside kvm ")
            print(kvm.getEntities())
            print("Result of configuring %s is %s" % (test_uuid, kvm.configureEntity(test_uuid)))

            import time
            time.sleep(10)

            print("Result of clean %s" % kvm.cleanEntity(test_uuid))
            print("Result of undefine %s" % kvm.undefineEntity(test_uuid))
            self.cache.remove(uri)

            print(self.cache)
            
        '''

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

