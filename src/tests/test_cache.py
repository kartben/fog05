import sys, os
sys.path.append(os.path.join(sys.path[0].rstrip("tests")))

import uuid
from DStore import *
from DController import *
import json


class TestCache():

    def __init__(self):
        self.uuid = uuid.uuid4()
        self.store = DStore(100, self.uuid)

        osuuid = uuid.uuid4()

        self.root = str("fos://<sys-id>/%s" % self.uuid)

        val = {'status': 'add', 'version': 1, 'description': 'linux plugin', 'plugin': 'here should be python object'}
        uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, 'linux', osuuid ))
        self.store.put(uri, val)

        val = {'plugins': [{'name': 'linux', 'version': 1, 'uuid': osuuid,
                           'type': 'os'}]}
        uri = uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
        self.store.put(uri, json.dumps(val))

        self.populateNodeInformation()


    def populateNodeInformation(self):

        node_info = {}

        node_info.update({'name': 'develop node'})
        uri = str('fos://<sys-id>/%s/' % self.uuid)
        self.store.put(uri, json.dumps(node_info))

    def test_observer(self, key, value):
        print ("##### I'M an Observer #####")
        print ("Change to %s : %s" % (key, value))
        print ("###########################")

    def main(self):

        print(self.store)


        uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
        #print (uri)
        all_plugins = json.loads(self.store.get(uri)[0].get(uri)).get('plugins')
        print(all_plugins)

        rt_uuid = uuid.uuid4()
        val = {'status': 'add', 'version': 1, 'description': 'test runtime', 'plugin': 'python obj'}
        uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, 'test runtime', rt_uuid))
        self.store.put(uri, val)

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

        exit(0)

        #################


if __name__=='__main__':
    agent = TestCache()
    agent.main()

