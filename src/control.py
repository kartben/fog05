from interfaces.Agent import Agent
from PluginLoader import PluginLoader
import uuid
import sys
from DStore import *
#from RedisLocalCache import RedisCache
import json


class Controll():

    def __init__(self):

        self.uuid=uuid.uuid4()
        sid = str(self.uuid)
        self.root = "fos://<sys-id>"
        self.home = str("fos://<sys-id>/%s" % sid)
        self.nodes = []
        # Notice that a node may have multiple caches, but here we are
        # giving the same id to the nodew and the cache
        self.store = DStore(sid, self.root, self.home, 1024)

    def nodeDiscovered(self, uri, value, v):
        value = json.loads(value)
        if uri != str('fos://<sys-id>/%s/' % self.uuid):
            print ("###########################")
            print ("###########################")
            print ("### New Node discovered ###")
            print ("UUID: %s" % value.get('uuid'))
            print ("Name: %s" % value.get('name'))
            print ("###########################")
            print ("###########################")
            self.nodes.append({value.get('uuid'): value})

    def main(self):

        #uri = str('fos://<sys-id>/%s/*' % self.uuid)
        #self.store.observe(uri, self.reactToCache)

        uri = str('fos://<sys-id>/*/')
        self.store.observe(uri, self.nodeDiscovered)


        vm_uuid = str(uuid.uuid4())

        vm_name = 'test'
        vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 128, 'disk_size': 5, 'base_image':
            'http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img'}

        entity_definition = {'status': 'define', 'name': vm_name, 'version': 1, 'entity_data': vm_definition}

        json_data = json.dumps(entity_definition)

        print("Press enter to define a vm")
        input()



        uri = str('fos://<sys-id>/0aa110af-698b-4297-a7d7-9c0ff1ffc72c/plugins/kvm-libvirt/9c7ffcee-031b-46be-9834'
                  '-8eb4b111fd2a/entity/%s' % vm_uuid)
        self.store.put(uri, json_data)


        print (self.store.get_value(str('fos://<sys-id>/0aa110af-698b-4297-a7d7-9c0ff1ffc72c/plugins/kvm-libvirt/9c7ffcee-031b-46be-9834'
                  '-8eb4b111fd2a/entity/%s' % vm_uuid)))

        print("Press enter to configure the vm")
        input()



        uri = str('fos://<sys-id>/0aa110af-698b-4297-a7d7-9c0ff1ffc72c/plugins/kvm-libvirt/9c7ffcee-031b-46be-9834'
                  '-8eb4b111fd2a/entity/%s#status=configure' % vm_uuid)
        self.store.dput(uri)

        print (self.store.get_value(
            str('fos://<sys-id>/0aa110af-698b-4297-a7d7-9c0ff1ffc72c/plugins/kvm-libvirt/9c7ffcee-031b-46be-9834'
                '-8eb4b111fd2a/entity/%s' % vm_uuid)))



        print("Press enter to configure the vm")
        input()


        input()

        exit(0)


        while True:
            time.sleep(100)






        #uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
        #all_plugins = json.loads(self.store.get(uri)).get('plugins')
        #print(all_plugins)

        '''

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']

        print (runtimes)

        print("locating kvm plugin")
        kvm = [x for x in runtimes if 'kvm' in x.get('name')][0]

        #print(kvm)
        uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, kvm.get('name'), kvm.get('uuid')))
        kvm = json.loads(self.store.get(uri))
        print(kvm)
        kvm = kvm.get('plugin')
        print (kvm)
        '''

        '''
        
        
        print("Press enter to define a vm")
        input()


        vm_uuid = str(uuid.uuid4())
        vm_name = 'test'

        vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 128, 'disk_size': 5, 'base_image':
            'http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img' }

        entity_definition = {'status': 'define', 'name': vm_name, 'version': 1, 'entity_data': vm_definition}

        json_data = json.dumps(entity_definition)
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, kvm.uuid, vm_uuid))
        self.store.put(uri, json_data)
        print (self.store)

        print("Press enter to configure the vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (self.uuid, kvm.uuid, vm_uuid))
        self.store.dput(uri)
        print (self.store)

        print("Press enter to start vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (self.uuid, kvm.uuid, vm_uuid))
        self.store.dput(uri)
        print (self.store)

        print("Press enter to stop vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' % (self.uuid, kvm.uuid, vm_uuid))
        self.store.dput(uri)
        print (self.store)

        print("Press enter to clean vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' % (self.uuid, kvm.uuid, vm_uuid))
        self.store.dput(uri)
        print (self.store)
        print("Press enter to undefine vm")
        input()

        json_data = json.dumps({'status': 'undefine'})
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, kvm.uuid, vm_uuid))
        self.store.put(uri, json_data)
        print (self.store)

        exit(0)
        
        
        
        '''



        #################


if __name__=='__main__':
    c = Controll()
    c.main()

