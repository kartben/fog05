import uuid
import sys
import os
sys.path.append(os.path.join(sys.path[0].rstrip("examples")))
from DStore import *
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


    def main(self):

        uri = str('afos://<sys-id>/*/')
        self.astore.observe(uri, self.nodeDiscovered)

        vm_uuid = str(uuid.uuid4())

        while len(self.nodes) < 1:
            time.sleep(2)

        self.show_nodes()

        vm_src_node = self.nodes.get(1)
        if vm_src_node is not None:
            vm_src_node = list(vm_src_node.keys())[0]

        input()

        vm_src_node = self.nodes.get(1)
        if vm_src_node is not None:
            vm_src_node = list(vm_src_node.keys())[0]

        self.vm_deploy(vm_src_node, vm_uuid)

        input()

        self.vm_destroy(vm_src_node, vm_uuid)

        input()

        exit(0)


if __name__ == '__main__':
    c = Controll()
    c.main()
