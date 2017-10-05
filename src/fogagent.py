from interfaces.Agent import Agent
from PluginLoader import PluginLoader
import uuid
import sys
from DDSCache import *
#from RedisLocalCache import RedisCache
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
        self.cache = DDSCache(100, self.uuid, DDSObserver())

        val = {'status': 'add', 'version': self.osPlugin.version, 'description': 'linux plugin', 'plugin': self.osPlugin}
        uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, self.osPlugin.name, self.osPlugin.uuid))
        self.cache.put(uri, val)

        val = {'plugins': [{'name': 'linux', 'version': self.osPlugin.version, 'uuid': str(self.osPlugin.uuid),
                           'type': 'os'}]}
        uri = uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
        self.cache.put(uri, json.dumps(val))

        self.populateNodeInformation()



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

            val = {'status': 'add', 'version': rt.version, 'description': str('runtime %s' % rt.name), 'plugin':rt}
            uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, rt.name, rt.uuid))
            self.cache.put(uri, val)

            val = {'plugins': [{'name': rt.name, 'version': rt.version, 'uuid': str(rt.uuid),
                                'type': 'runtime'}]}
            uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
            self.cache.dput(uri, json.dumps(val))

            return rt
        else:
            return None

    def loadNetworkPlugin(self, plugin_name):
        net = self.pl.locatePlugin(plugin_name)
        if net is not None:
            net = self.pl.loadPlugin(net)
            net = net.run(agent=self)
            self.rtPlugins.update({net.uuid: net})

            val = {'status': 'add', 'version': net.version, 'description': str('runtime %s' % net.name), 'plugin':net}
            uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, net.name, net.uuid))
            self.cache.put(uri, val)

            val = {'plugins': [{'name': net.name, 'version': net.version, 'uuid': str(net.uuid),
                                'type': 'network'}]}
            uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
            self.cache.dput(uri, json.dumps(val))

            return net
        else:
            return None

    def populateNodeInformation(self):

        node_info = {}
        node_info.update({'uuid': str(self.uuid)})
        node_info.update({'name': 'develop node'})

        node_info.update({'cpu': self.osPlugin.getProcessorInformation()})
        node_info.update({'ram': self.osPlugin.getMemoryInformation()})
        node_info.update({'disks': self.osPlugin.getDisksInformation()})
        node_info.update({'network': self.osPlugin.getNetworkInformations()})

        uri = str('fos://<sys-id>/%s/' % self.uuid)
        self.cache.put(uri, json.dumps(node_info))

    def main(self):

        print(self.cache)

        self.loadRuntimePlugin('RuntimeLibVirt')
        self.loadNetworkPlugin('brctl')

        print (self.cache)

        #exit(0)

        uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
        print (uri)
        all_plugins = json.loads(self.cache.get(uri)[0].get(uri)).get('plugins')
        print(all_plugins)

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']

        print (runtimes)

        print("locating kvm plugin")
        kvm = [x for x in runtimes if 'kvm' in x.get('name')][0]

        print(kvm)
        uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, kvm.get('name'), kvm.get('uuid')))
        kvm = self.cache.get(uri)[0].get(uri)
        print(kvm)
        kvm = kvm.get('plugin')
        print (kvm)
        kvm.startRuntime()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/*' % (self.uuid, kvm.uuid))
        self.cache.observe(uri, kvm.reactToCache)


        print("Press enter to define a vm")
        input()

        vm_uuid = str(uuid.uuid4())
        vm_name = 'test'

        vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 512, 'disk_size': 5, 'base_image':
            'http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img' }

        entity_definition = {'status': 'define', 'name': vm_name, 'version': 1, 'entity_data': vm_definition}

        json_data = json.dumps(entity_definition)
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, kvm.uuid, vm_uuid))
        self.cache.put(uri, json_data)
        print (self.cache)

        print (kvm.getEntities())


        print("Press enter to configure the vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (self.uuid, kvm.uuid, vm_uuid))
        self.cache.dput(uri)
        print (self.cache)

        print("Press enter to start vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (self.uuid, kvm.uuid, vm_uuid))
        self.cache.dput(uri)
        print (self.cache)

        print("Press enter to stop vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' % (self.uuid, kvm.uuid, vm_uuid))
        self.cache.dput(uri)
        print (self.cache)

        print("Press enter to clean vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' % (self.uuid, kvm.uuid, vm_uuid))
        self.cache.dput(uri)
        print (self.cache)
        print("Press enter to undefine vm")
        input()

        json_data = json.dumps({'status': 'undefine'})
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, kvm.uuid, vm_uuid))
        self.cache.put(uri, json_data)
        print (self.cache)

        exit(0)




if __name__=='__main__':
    agent = FogAgent()
    agent.main()

