import sys, os
sys.path.append(os.path.join(sys.path[0].rstrip("tests")))

import uuid
from DStore import *
from DController import *
import json


class TestCache():

    def __init__(self):
        self.uuid = uuid.uuid4()
        sid = str(self.uuid)


        # Desidered Store. containing the desidered state
        self.droot = "dfos://<sys-id>"
        self.dhome = str("dfos://<sys-id>/%s" % sid)
        self.dstore = DStore(sid, self.droot, self.dhome, 1024)

        # Actual Store, containing the Actual State
        self.aroot = "afos://<sys-id>"
        self.ahome = str("afos://<sys-id>/%s" % sid)
        self.astore = DStore(sid, self.aroot, self.ahome, 1024)

        self.nodes = {}

        self.populateNodeInformation()

    def populateNodeInformation(self):

        node_info = {}

        node_info.update({'name': 'develop node'})
        uri = str('%s/' % self.ahome)
        self.astore.put(uri, json.dumps(node_info))

    def test_observer_actual(self, key, value,v):
        print ("##################################")
        print ("##### I'M an Observer ACTUAL #####")
        print ("## Key: %s" % key)
        print ("## Value: %s" % value)
        print ("## V: %s" % v)
        print("##################################")
        print("##################################")

    def test_observer_desidered(self, key, value,v):
        print ("#####################################")
        print ("##### I'M an Observer DESIDERED #####")
        print ("## Key: %s" % key)
        print ("## Value: %s" % value)
        print ("## V: %s" % v)
        print("#####################################")
        print("#####################################")


    def nodeDiscovered(self, uri, value, v = None):
        value = json.loads(value)
        if uri != str('fos://<sys-id>/%s/' % self.uuid):
            print ("###########################")
            print ("###########################")
            print ("### New Node discovered ###")
            print ("UUID: %s" % value.get('uuid'))
            print ("Name: %s" % value.get('name'))
            print ("###########################")
            print ("###########################")
            self.nodes.update({ len(self.nodes)+1 : {value.get('uuid'): value}})

    def show_nodes(self):
        for k in self.nodes.keys():
            n = self.nodes.get(k)
            id = list(n.keys())[0]
            print("%d - %s : %s" % (k, n.get(id).get('name'), id))

    def main(self):
        uri = str('afos://<sys-id>/*/')
        self.astore.observe(uri, self.nodeDiscovered)

        uri = str('dfos://<sys-id>/*')
        self.dstore.observe(uri, self.test_observer_desidered)

        uri = str('afos://<sys-id>/*')
        self.astore.observe(uri, self.test_observer_actual)

        print("Putting on dstore")
        val = {'value': "some value"}
        uri = str('%s/test1' % self.dhome)
        self.dstore.put(uri, json.dumps(val))

        val = {'value2': "some value2"}
        uri = str('%s/test2' % self.dhome)
        self.dstore.put(uri, json.dumps(val))

        val = {'value3': "some value3"}
        uri = str('%s/test3' % self.dhome)
        self.dstore.put(uri, json.dumps(val))

        print("Putting on astore")

        val = {'actual value': "some value"}
        uri = str('%s/test1' % self.ahome)
        self.astore.put(uri, json.dumps(val))

        val = {'actual value2': "some value2"}
        uri = str('%s/test2' % self.ahome)
        self.astore.put(uri, json.dumps(val))

        val = {'actual value32': "some value3"}
        uri = str('%s/test3' % self.ahome)
        self.astore.put(uri, json.dumps(val))

        while len(self.nodes) < 1:
            time.sleep(2)

        self.show_nodes()

        print("My UUID is %s" % self.uuid)

        print("###################################### Desidered Store ######################################")
        print(self.dstore)
        print("#############################################################################################")

        print("###################################### Actual Store #########################################")
        print(self.astore)
        print("#############################################################################################")







        '''        print(self.store)


        uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
        #print (uri)
        v = self.store.get(uri)

        all_plugins = json.loads(v).get('plugins')

        print(">> Plugins: " + str(all_plugins))

        rt_uuid = uuid.uuid4()
        val = {'status': 'add', 'version': 1, 'description': 'test runtime', 'plugin': 'python obj'}
        uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, 'test runtime', rt_uuid))
        self.store.put(uri, json.dumps(val))
        
        self.store.put(uri, json.dumps(val))
        val = {'plugins': [{'name': 'runtime', 'version': 1, 'uuid': str(rt_uuid),
                            'type': 'runtime'}]}
        uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
        self.store.dput(uri, json.dumps(val))

        print (self.store)


        uri = str('fos://<sys-id>/%s/runtime/%s/entity/*' % (self.uuid, rt_uuid))
        self.store.observe(uri, self.test_observer)


        print("Press enter to define a vm")
        input()

        vm_uuid = str(uuid.uuid4())
        vm_name = 'test'

        vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 512, 'disk_size': 5, 'base_image':
            'http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img' }

        entity_definition = {'status': 'define', 'name': vm_name, 'version': 1, 'entity_data': vm_definition}

        json_data = json.dumps(entity_definition)
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, rt_uuid, vm_uuid))
        self.store.put(uri, json_data)
        print (self.store)


        print("Press enter to configure the vm")

        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (self.uuid, rt_uuid, vm_uuid))
        self.store.dput(uri)

        print (self.store)


        print("Press enter to start vm")

        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (self.uuid, rt_uuid, vm_uuid))
        self.store.dput(uri)
        print (self.store)

        print("Press enter to stop vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' % (self.uuid, rt_uuid, vm_uuid))
        self.store.dput(uri)
        print (self.store)

        print("Press enter to clean vm")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' % (self.uuid, rt_uuid, vm_uuid))
        self.store.dput(uri)
        print (self.store)
        print("Press enter to undefine vm")
        input()

        json_data = json.dumps({'status': 'undefine'})
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.uuid, rt_uuid, vm_uuid))
        self.store.put(uri, json_data)
        print (self.store)

        '''
        input()
        exit(0)

        #################


if __name__=='__main__':
    agent = TestCache()
    agent.main()

