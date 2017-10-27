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

    def read_file(self, file_path):
        with open(file_path,'r') as f:
            data = f.read()
        return data

    def show_nodes(self):
        for k in self.nodes.keys():
            n = self.nodes.get(k)
            id = list(n.keys())[0]
            print("%d - %s : %s" % (k, n.get(id).get('name'), id))

    def deploy_application(self, node_uuid):

        val = {'plugins': [{'name': 'KVMLibvirt', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        self.dstore.dput(uri, json.dumps(val))

        time.sleep(1)

        val = {'plugins': [{'name': 'native', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        self.dstore.dput(uri, json.dumps(val))

        time.sleep(1)


        app_uuid = str(uuid.uuid4())

        cinit = self.read_file('./cloud_init_demo')
        sshk = self.read_file('/home/ubuntu/key.pub')
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

        uri_vm = str('dfos://<sys-id>/%s/onboard/%s/%s' % (node_uuid, app_uuid, "nginx"))
        uri_na = str('dfos://<sys-id>/%s/onboard/%s/%s' % (node_uuid, app_uuid, app_name))
        json_data = json.dumps(na)
        self.dstore.put(uri_na, json_data)
        json_data = json.dumps(vm)
        self.dstore.put(uri_vm, json_data)



        app = {"name":"demo", "description":"simple nginx+web demo",
        "components":[{ "name":"nginx","need":[],"proximity":{},"manifest":uri_vm},
                {"name":"browser","need":["nginx"],"proximity":{},"manifest":uri_na}]}

        json_data = json.dumps(app)

        time.sleep(1)

        uri = str('dfos://<sys-id>/%s/onboard/%s/' % (node_uuid, app_uuid))
        self.dstore.put(uri, json_data)

    def main(self):

        uri = str('afos://<sys-id>/*/')
        self.astore.observe(uri, self.nodeDiscovered)

        vm_uuid = str(uuid.uuid4())

        while len(self.nodes) < 1:
            time.sleep(2)

        self.show_nodes()

        dst_node = self.nodes.get(1)
        if dst_node is not None:
            dst_node = list(dst_node.keys())[0]

        input()

        self.deploy_application(dst_node)


        input()

        exit(0)


if __name__ == '__main__':
    c = Controll()
    c.main()
