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

        '''
        Creating the two stores
        
        afos://...  Actual State Store
        In this store you can find all the actual data of the node, this store is written by
        plugins and by the fogagent for update the store after a request.
        All other nodes can read or observe only this store.
        
        
        dfos://... Desidered State Store
        In this store other nodes write the command/request, all plugins and the agent observe this store,
        in a way that they can react to a desidered state
        
        '''


        self.droot = "dfos://<sys-id>"
        self.dhome = str("dfos://<sys-id>/%s" % sid)
        self.dstore = DStore(sid, self.droot, self.dhome, 1024)

        self.aroot = "afos://<sys-id>"
        self.ahome = str("afos://<sys-id>/%s" % sid)
        self.astore = DStore(sid, self.aroot, self.ahome, 1024)

        self.nodes = {}




    def nodeDiscovered(self, uri, value, v = None):
        '''

        This is an observer for discover new nodes on the network
        It is called by the DStore object where it was registered.
        If a new node is discovered it will be added to the self.nodes dict

        :param uri:
        :param value:
        :param v:
        :return:
        '''
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
        '''
        Simply method to read a file
        :param file_path: The file path
        :return: The file content
        '''
        with open(file_path,'r') as f:
            data = f.read()
        return data


    def show_nodes(self):
        '''
        Print all nodes discovered by this script

        :return:
        '''
        for k in self.nodes.keys():
            n = self.nodes.get(k)
            id = list(n.keys())[0]
            print("%d - %s : %s" % (k, n.get(id).get('name'), id))


    def vm_deploy(self, node_uuid, vm_uuid):
        '''
        This method make the destination node load the correct plugins,
        and then deploy the vm to the node

        :param node_uuid:
        :param vm_uuid:
        :return:
        '''

        print("Make node load kvm plugin")

        val = {'plugins': [{'name': 'KVMLibvirt', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        print(uri)
        self.dstore.dput(uri, json.dumps(val))  # Writing to the desidered store of the destination node
                                                # the manifest of the plugin to load, in this case KVM

        time.sleep(1)
        val = {'plugins': [{'name': 'brctl', 'version': 1, 'uuid': '',
                            'type': 'network', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        self.dstore.dput(uri, json.dumps(val))  # Writing to the desidered store of the destination node
                                                # the manifest of the plugin to load, in this case bridge-utils

        time.sleep(1)

        print("Looking if kvm plugin loaded")

        # reading from the actual store of the node if the KVM plugin was loaded

        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)  # reading from actual state store
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

        cinit = None  # or self.readFile(cloud_init_file_path) # KVM plugin support cloudinit initializzation
        sshk = None   # or self.readFile(pub key file path)       #

        ##### OTHER IMAGES USED
        #virt-cirros-0.3.4-x86_64-disk.img
        #cirros-0.3.5-x86_64-disk.img
        #xenial-server-cloudimg-amd64-disk1.img
        #####


        # creating the manifest for the vm
        vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 512, 'disk_size': 10, 'base_image':
            'http://192.168.1.142/virt-cirros-0.3.4-x86_64-disk.img', 'networks': [{
            'mac': "d2:e3:ed:6f:e3:ef", 'br_name': "virbr0"}], "user-data": cinit, "ssh-key": sshk}

        entity_definition = {'status': 'define', 'name': vm_name, 'version': 1, 'entity_data': vm_definition}

        json_data = json.dumps(entity_definition)

        print("Press enter to define a vm")
        input()

        # writing the manifest to the desidered store of the destination node
        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, kvm.get('uuid'), vm_uuid))
        self.dstore.put(uri, json_data)

        # busy waiting for the vm to state change
        while True:
            print("Waiting vm defined...")
            time.sleep(1)
            #reading state from actual store
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
            vm_info = json.loads(self.astore.get(uri))
            if vm_info is not None and vm_info.get("status") == "defined":
                    break

        # using a dput (delta put) to only update the vm state, so cause a state transition
        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (node_uuid, kvm.get('uuid'), vm_uuid))
        self.dstore.dput(uri)

        # waiting the vm sto state change
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


        # load the plugin uuid from the actual store of the destination node
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

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, kvm.get('uuid'), vm_uuid))
        self.dstore.remove(uri)

    def main(self):

        # registering an observer for all actual store root in this system
        # this allow the discovery of new nodes
        uri = str('afos://<sys-id>/*/')
        self.astore.observe(uri, self.nodeDiscovered)



        vm_uuid = str(uuid.uuid4())

        # simple busy wait for a node to appear
        while len(self.nodes) < 1:
            time.sleep(2)

        self.show_nodes()

        input()

        # getting the node uuid
        vm_dst_node = self.nodes.get(1)
        if vm_dst_node is not None:
            vm_dst_node = list(vm_dst_node.keys())[0]

        # deploy the vm
        self.vm_deploy(vm_dst_node, vm_uuid)

        input()

        # offload the vm
        self.vm_destroy(vm_dst_node, vm_uuid)

        input()

        exit(0)


if __name__ == '__main__':
    c = Controll()
    c.main()
