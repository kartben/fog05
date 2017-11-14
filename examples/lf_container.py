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


    def container_deploy(self, node_uuid, container_uuid):
        '''
        This method make the destination node load the correct plugins,
        and then deploy the container to the node

        :param node_uuid:
        :param container_uuid:
        :return:
        '''

        print("Make node load lxd plugin")

        val = {'plugins': [{'name': 'LXD', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        print(uri)
        self.dstore.dput(uri, json.dumps(val))  # Writing to the desidered store of the destination node
                                                # the manifest of the plugin to load, in this case Kcontainer

        time.sleep(2)
        val = {'plugins': [{'name': 'brctl', 'version': 1, 'uuid': '',
                            'type': 'network', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        self.dstore.dput(uri, json.dumps(val))  # Writing to the desidered store of the destination node
                                                # the manifest of the plugin to load, in this case bridge-utils

        time.sleep(1)

        print("Looking if lxd plugin loaded")

        # reading from the actual store of the node if the Kcontainer plugin was loaded

        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)  # reading from actual state store
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating LXD plugin")
        search = [x for x in runtimes if 'LXD' in x.get('name')]
        if len(search) == 0:
            print ("Plugin was not loaded")
            exit()
        else:
            lxd = search[0]

        container_name = 'test'

        cinit = None  # or self.readFile(cloud_init_file_path) # Kcontainer plugin support cloudinit initializzation
        sshk = None   # or self.readFile(pub key file path)       #

        ##### OTHER IMAGES USED
        #virt-cirros-0.3.4-x86_64-disk.img
        #cirros-0.3.5-x86_64-disk.img
        #xenial-server-cloudimg-amd64-disk1.img
        #####


        # creating the manifest for the container
        container_definition = {'name': container_name, 'uuid': container_uuid, 'base_image':
            'http://172.16.7.128/ubuntu_container.tar.xz', 'networks': [{
            'mac': "d2:e3:ed:6f:e3:ef", 'intf_name': "br0"}], "user-data": cinit, "ssh-key": sshk}

        entity_definition = {'status': 'define', 'name': container_name, 'version': 1, 'entity_data': container_definition}

        json_data = json.dumps(entity_definition)

        print("Press enter to define a container")
        input()

        # writing the manifest to the desidered store of the destination node
        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, lxd.get('uuid'), container_uuid))
        self.dstore.put(uri, json_data)

        # busy waiting for the container to state change
        while True:
            print("Waiting container defined...")
            time.sleep(1)
            #reading state from actual store
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, lxd.get('uuid'), container_uuid))
            container_info = json.loads(self.astore.get(uri))
            if container_info is not None and container_info.get("status") == "defined":
                    break

        # using a dput (delta put) to only update the container state, so cause a state transition
        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (node_uuid, lxd.get('uuid'), container_uuid))
        self.dstore.dput(uri)

        # waiting the container sto state change
        while True:
            print("Waiting container configured...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, lxd.get('uuid'), container_uuid))
            container_info = json.loads(self.astore.get(uri))
            if container_info is not None and container_info.get("status") == "configured":
                    break



        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (node_uuid, lxd.get('uuid'), container_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting container to boot...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, lxd.get('uuid'), container_uuid))
            container_info = json.loads(self.astore.get(uri))
            if container_info is not None and container_info.get("status") == "run":
                    break

        print("container is running on node")

    def container_destroy(self, node_uuid, container_uuid):


        # load the plugin uuid from the actual store of the destination node
        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating lxd plugin")
        search = [x for x in runtimes if 'LXD' in x.get('name')]
        if len(search) == 0:
            print ("Plugin was not loaded")
            exit()
        else:
            lxd = search[0]


        print("Press enter to stop container")
        input()

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' % (node_uuid, lxd.get('uuid'), container_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting container to be stopped...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, lxd.get('uuid'), container_uuid))
            container_info = json.loads(self.astore.get(uri))
            if container_info is not None and container_info.get("status") == "stop":
                break

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' %
                  (node_uuid, lxd.get('uuid'), container_uuid))
        self.dstore.dput(uri)

        while True:
            print("Waiting cleaned...")
            time.sleep(1)
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, lxd.get('uuid'), container_uuid))
            container_info = json.loads(self.astore.get(uri))
            if container_info is not None and container_info.get("status") == "cleaned":
                break

        # TODO this should be done with a remove
        json_data = json.dumps({'status': 'undefine'})
        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, lxd.get('uuid'), container_uuid))
        self.dstore.dput(uri, json_data)
        #self.dstore.remove(uri)


    def main(self):

        # registering an observer for all actual store root in this system
        # this allow the discovery of new nodes
        uri = str('afos://<sys-id>/*/')
        self.astore.observe(uri, self.nodeDiscovered)



        container_uuid = str(uuid.uuid4())

        # simple busy wait for a node to appear
        while len(self.nodes) < 1:
            time.sleep(2)

        self.show_nodes()

        input()

        # getting the node uuid
        container_dst_node = self.nodes.get(1)
        if container_dst_node is not None:
            container_dst_node = list(container_dst_node.keys())[0]

        # deploy the container
        self.container_deploy(container_dst_node, container_uuid)

        input()

        # offload the container
        self.container_destroy(container_dst_node, container_uuid)

        input()

        exit(0)


if __name__ == '__main__':
    c = Controll()
    c.main()
