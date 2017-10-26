from interfaces.Agent import Agent
from PluginLoader import PluginLoader
import uuid
import sys
from DStore import *
# from RedisLocalCache import RedisCache
import json
import time


class Controll():
    def __init__(self):
        self.uuid = uuid.uuid4()
        sid = str(self.uuid)

        self.droot = "dfos://<sys-id>"
        self.dhome = str("dfos://<sys-id>/%s" % sid)
        self.dstore = DStore(sid, self.droot, self.dhome, 1024)

        self.aroot = "afos://<sys-id>"
        self.ahome = str("afos://<sys-id>/%s" % sid)
        self.astore = DStore(sid, self.aroot, self.ahome, 1024)

        self.nodes = {}




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


    def readFile(self, file_path):
        with open(file_path,'r') as f:
            data = f.read()
        return data


    def show_nodes(self):
        for k in self.nodes.keys():
            n = self.nodes.get(k)
            id = list(n.keys())[0]
            print("%d - %s : %s" % (k, n.get(id).get('name'), id))

    def lf_native(self, node_uuid):

        print("Make node load native plugin")

        val = {'plugins': [{'name': 'native', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('fos://<sys-id>/%s/plugins' % node_uuid)
        self.store.dput(uri, json.dumps(val))

        time.sleep(1)

        print("Looking if native plugin loaded")

        uri = str('fos://<sys-id>/%s/plugins' % node_uuid)
        all_plugins = json.loads(self.store.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating native plugin")
        search = [x for x in runtimes if 'native' in x.get('name')]
        if len(search) == 0:
            print ("Plugin was not loaded")
            exit()
        else:
            native = search[0]
        app_name = 'Browser'
        app_uuid = str(uuid.uuid4())
        app_definition = {'name': app_name, 'command': 'firefox', 'args': ['172.16.7.131'], 'uuid': app_uuid}
        entity_definition = {'status': 'define', 'name': app_name, 'version': 1, 'entity_data': app_definition}

        json_data = json.dumps(entity_definition)

        print("Press enter to define the native")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), app_uuid))
        self.store.put(uri, json_data)

        print("Press enter to configure the native")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.store.dput(uri)

        print("Press enter to start the native")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.store.dput(uri)

        print("Press enter to stop the native")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.store.dput(uri)

        print("Press enter to clean the native")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.store.dput(uri)

        print("Press enter to undefine the native")
        input()

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=undefine' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.store.dput(uri)

    def vm_deploy(self, node_uuid, vm_uuid):
        print("Make node load kvm plugin")

        val = {'plugins': [{'name': 'KVMLibvirt', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        print(uri)
        #print(self.dstore.get(uri))

        self.dstore.dput(uri, json.dumps(val))

        time.sleep(1)
        val = {'plugins': [{'name': 'brctl', 'version': 1, 'uuid': '',
                            'type': 'network', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        self.dstore.dput(uri, json.dumps(val))

        time.sleep(1)

        print("Looking if kvm plugin loaded")

        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating kvm plugin")
        search = [x for x in runtimes if 'KVMLibvirt' in x.get('name')]
        if len(search) == 0:
            print ("Plugin was not loaded")
            exit()
        else:
            kvm = search[0]

        vm_name = 'test'

        cinit = None  #self.readFile('./cloud_init_demo')
        sshk = self.readFile('./key.pub')


        #virt-cirros-0.3.4-x86_64-disk.img
        #cirros-0.3.5-x86_64-disk.img
        #xenial-server-cloudimg-amd64-disk1.img

        vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 512, 'disk_size': 10, 'base_image':
            'http://172.16.7.128/virt-cirros-0.3.4-x86_64-disk.img', 'networks': [{
            'mac': "d2:e3:ed:6f:e3:ef", 'intf_name': "br0"}], "user-data": cinit, "ssh-key": sshk}

        entity_definition = {'status': 'define', 'name': vm_name, 'version': 1, 'entity_data': vm_definition}

        json_data = json.dumps(entity_definition)

        print("Press enter to define a vm")
        input()

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, kvm.get('uuid'), vm_uuid))
        self.dstore.put(uri, json_data)

        while True:
            print("Waiting vm defined...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "defined":
                    break

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (node_uuid, kvm.get('uuid'), vm_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting vm configured...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "configured":
                    break



        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (node_uuid, kvm.get('uuid'), vm_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting vm to boot...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "run":
                    break

        print("vm is running on node")

    def vm_destroy(self, node_uuid, vm_uuid):

        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating kvm plugin")
        search = [x for x in runtimes if 'KVMLibvirt' in x.get('name')]
        if len(search) == 0:
            print ("Plugin was not loaded")
            exit()
        else:
            kvm = search[0]


        print("Press enter to stop vm")
        input()

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' % (node_uuid, kvm.get('uuid'), vm_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting vm to be stopped...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "stop":
                break

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' %
                  (node_uuid, kvm.get('uuid'), vm_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting cleaned...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "cleaned":
                break

        json_data = json.dumps({'status': 'undefine'})
        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' %
                  (node_uuid, kvm.get('uuid'), vm_uuid))
        self.dstore.dput(uri, json_data)


    def deploy_application(self, node_uuid):

        val = {'plugins': [{'name': 'KVMLibvirt', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        self.dstore.dput(uri, json.dumps(val))

        time.sleep(1)

        val = {'plugins': [{'name': 'native', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('fos://<sys-id>/%s/plugins' % node_uuid)
        self.store.dput(uri, json.dumps(val))

        time.sleep(1)


        app_uuid = str(uuid.uuid4())

        cinit = self.readFile('./cloud_init_demo')
        sshk = self.readFile('/home/ubuntu/key.pub')
        vm_name = 'nginx'
        vm_uuid = str(uuid.uuid4())
        vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 512, 'disk_size': 10, 'base_image':
            'http://172.16.7.128/xenial-server-cloudimg-amd64-disk1.img', 'networks': [{
            'mac': "d2:e3:ed:6f:e3:ef", 'intf_name': "br0"}], "user-data": cinit, "ssh-key": sshk}



        vm = {
            "name":"nginx",
            "description":"mysql web server",
            "version" : 3,
            "type":"kvm",
            "entity_description":vm_definition,
            "accelerators":[],
            "io":[]
        }

        app_name = 'browser'
        app_uuid = str(uuid.uuid4())
        app_definition = {'name': app_name, 'command': 'firefox', 'args': ['172.16.7.131'], 'uuid': app_uuid}

        na = {
            "name": "browser",
            "description": "firefox",
            "version": 3,
            "type": "native",
            "entity_description": app_definition,
            "accelerators": [],
            "io": []
        }

        uri_vm = str('fos://<sys-id>/%s/applications/%s/%s' % (node_uuid, app_uuid,"nginx"))
        uri_na = str('fos://<sys-id>/%s/applications/%s/%s' % (node_uuid, app_uuid, app_name))
        json_data = json.dumps(na)
        self.store.put(uri_na, json_data)
        json_data = json.dumps(vm)
        self.store.put(uri_vm, json_data)



        app = {"name":"demo", "description":"simple nginx+web demo",
        "components":[{ "name":"nginx","need":[],"proximity":{},"manifest":uri_vm},
                {"name":"browser","need":[],"proximity":{},"manifest":uri_na}]}

        json_data = json.dumps(app)

        uri = str('fos://<sys-id>/%s/applications/%s/' % (node_uuid, app_uuid))
        self.store.put(uri, json_data)


    def migrate_vm(self, src, dst, vm_uuid):

        uri = str('afos://<sys-id>/%s/plugins' % src)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating kvm plugin")
        search = [x for x in runtimes if 'KVMLibvirt' in x.get('name')]
        if len(search) == 0:
            print ("Plugin was not loaded")
            exit()
        else:
            kvm_src = search[0]
        uri = str('afos://<sys-id>/%s/runtime/%s/entity/%s' % (src, kvm_src.get('uuid'), vm_uuid))
        vm_info = json.loads(self.astore.get(uri))
        print (vm_info)

        input()

        vm_info.update({"status": "taking_off"})
        vm_info.update({"dst": dst})

        vm_info_dst = vm_info.copy()
        vm_info_dst.update({"status": "landing"})

        print(vm_info)
        print(vm_info_dst)

        input()

        print("Make node load kvm plugin")

        val = {'plugins': [{'name': 'KVMLibvirt', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % dst)
        self.dstore.put(uri, json.dumps(val))

        time.sleep(1)
        val = {'plugins': [{'name': 'brctl', 'version': 1, 'uuid': '',
                            'type': 'network', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % dst)
        self.dstore.put(uri, json.dumps(val))

        time.sleep(1)

        print("Looking if kvm plugin loaded")

        uri = str('afos://<sys-id>/%s/plugins' % dst)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating kvm plugin")
        search = [x for x in runtimes if 'KVMLibvirt' in x.get('name')]
        if len(search) == 0:
            print ("Plugin was not loaded")
            exit()
        else:
            kvm_dst = search[0]

        uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (dst, kvm_dst.get('uuid'), vm_uuid))

        json_data = json.dumps(vm_info_dst)

        print("Press enter to migrate a vm")
        input()

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (dst, kvm_dst.get('uuid'), vm_uuid))
        self.dstore.put(uri, json_data)

        json_data = json.dumps(vm_info)
        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (src, kvm_src.get('uuid'), vm_uuid))
        self.dstore.dput(uri, json_data)

        input("press enter to destroy vm")
        self.vm_destroy(dst, vm_uuid)





    def main(self):

        uri = str('afos://<sys-id>/*/')
        self.astore.observe(uri, self.nodeDiscovered)

        vm_uuid = str(uuid.uuid4())

        while len(self.nodes) < 2:
            time.sleep(2)

        self.show_nodes()


        # print("###################################### Desidered Store ######################################")
        # print(self.dstore)
        # print("#############################################################################################")
        #
        # print("###################################### Actual Store #########################################")
        # print(self.astore)
        # print("#############################################################################################")

        input()

        vm_src_node = self.nodes.get(1)
        if vm_src_node is not None:
            vm_src_node = list(vm_src_node.keys())[0]




        vm_dst_node = self.nodes.get(2)
        if vm_dst_node is not None:
            vm_dst_node = list(vm_dst_node.keys())[0]

        vm_uuid = str(uuid.uuid4())

        self.vm_deploy(vm_src_node, vm_uuid)

        input()

        self.migrate_vm(vm_src_node, vm_dst_node, vm_uuid)



        '''
        n = int(input("Select node for vm deploy: "))

        node_uuid = self.nodes.get(n)
        if node_uuid is not None:
            node_uuid = list(node_uuid.keys())[0]
            if node_uuid is not None:
                pass
        else:
            exit()

        #self.deploy_application(node_uuid)



        vm_node = node_uuid

        self.vm_deploy(vm_node, vm_uuid)

        self.show_nodes()

        n = int(input("Select node for native app deploy: "))

        node_uuid = self.nodes.get(n)
        if node_uuid is not None:
            node_uuid = list(node_uuid.keys())[0]
            if node_uuid is not None:
                pass
        else:
            exit()

        self.lf_native(node_uuid)

        input("Press enter to destroy vm")

        self.vm_destroy(vm_node, vm_uuid)
        #########
        '''

        input()

        exit(0)


if __name__ == '__main__':
    c = Controll()
    c.main()
