import uuid
import sys
import os
from fog05.DStore import *
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
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        self.dstore.dput(uri, json.dumps(val))

        time.sleep(1)

        print("Looking if native plugin loaded")

        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating native plugin")
        search = [x for x in runtimes if 'native' in x.get('name')]
        if len(search) == 0:
            print ("Plugin was not loaded")
            exit()
        else:
            native = search[0]
        app_name = 'hello_world'
        app_uuid = str(uuid.uuid4())
        app_definition = {'name': app_name, 'source': 'https://www.dropbox.com/s/pr6cj3e58j4xw6k/prova.zip',
                        'command': 'hello', 'args': [], 'uuid': app_uuid}
        entity_definition = {'status': 'define', 'name': app_name, 'version': 1, 'entity_data': app_definition}

        json_data = json.dumps(entity_definition)

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), app_uuid))
        self.dstore.put(uri, json_data)

        while True:
            print("Waiting native to defined...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), app_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "defined":
                break

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting native to defined...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), app_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "configured":
                break

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting native to defined...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), app_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "run":
                break

        print("Press enter to stop the native")
        input()

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting native to defined...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), app_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "stop":
                break

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting native to defined...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), app_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "cleaned":
                break

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=undefine' %
                  (node_uuid, native.get('uuid'), app_uuid))
        self.dstore.dput(uri)


    def main(self):

        uri = str('afos://<sys-id>/*/')
        self.astore.observe(uri, self.nodeDiscovered)

        while len(self.nodes) < 1:
            time.sleep(2)

        self.show_nodes()

        na_node = self.nodes.get(1)
        if na_node is not None:
            na_node = list(na_node.keys())[0]

        input()


        self.lf_native(na_node)

        input()

        exit(0)


if __name__ == '__main__':
    c = Controll()
    c.main()
