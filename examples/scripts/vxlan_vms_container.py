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

    def nodeDiscovered(self, uri, value, v=None):
        value = json.loads(value)
        if uri != str('fos://<sys-id>/%s/' % self.uuid):
            print("###########################")
            print("###########################")
            print("### New Node discovered ###")
            print("UUID: %s" % value.get('uuid'))
            print("Name: %s" % value.get('name'))
            print("###########################")
            print("###########################")
            self.nodes.update({len(self.nodes) + 1: {value.get('uuid'): value}})

    def read_file(self, file_path):
        with open(file_path, 'r') as f:
            data = f.read()
        return data

    def show_nodes(self):
        for k in self.nodes.keys():
            n = self.nodes.get(k)
            id = list(n.keys())[0]
            print("%d - %s : %s" % (k, n.get(id).get('name'), id))

    def vm_deploy(self, node_uuid, vm_uuid, net_uuid):
        print("Make node load kvm plugin")

        val = {'plugins': [{'name': 'KVMLibvirt', 'version': 1, 'uuid': '',
                            'type': 'runtime', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        print(uri)
        # print(self.dstore.get(uri))

        self.dstore.dput(uri, json.dumps(val))


        time.sleep(1)

        print("Looking if kvm plugin loaded")

        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating kvm plugin")
        search = [x for x in runtimes if 'KVMLibvirt' in x.get('name')]
        if len(search) == 0:
            print("Plugin was not loaded")
            exit()
        else:
            kvm = search[0]

        vm_name = 'test'

        cinit = None  # self.read_file(os.path.join(sys.path[0], 'etc', 'cloud_init_demo'))
        sshk = None #self.read_file(os.path.join(sys.path[0], 'etc', 'example_key.pub'))

        # virt-cirros-0.3.4-x86_64-disk.img
        # cirros-0.3.5-x86_64-disk.img
        # xenial-server-cloudimg-amd64-disk1.img
        # 192.168.1.142
        # 172.16.7.128
        #br_name = str("br-%s" % net_uuid.split('-')[0])

        vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 512, 'disk_size': 10, 'base_image':
            'http://192.168.1.142/brain.qcow2', 'networks': [{'network_uuid': net_uuid}],
            "user-data": cinit, "ssh-key": sshk}

        entity_definition = {'status': 'define', 'name': vm_name, 'version': 1, 'entity_data': vm_definition}

        json_data = json.dumps(entity_definition)

        #print("Press enter to define a vm")
        #input()

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
            print("Plugin was not loaded")
            exit()
        else:
            kvm = search[0]

        #print("Press enter to stop vm")
        #input()

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

    def container_deploy(self, node_uuid, container_uuid, manifest):
        # container_uuid, net_uuid, image_name, gw=False):
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

        time.sleep(1)

        print("Looking if lxd plugin loaded")

        # reading from the actual store of the node if the Kcontainer plugin was loaded

        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)  # reading from actual state store
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')

        runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
        print("locating LXD plugin")
        search = [x for x in runtimes if 'LXD' in x.get('name')]
        if len(search) == 0:
            print("Plugin was not loaded")
            exit()
        else:
            lxd = search[0]
        image_name = manifest.get('base_image')
        container_name = image_name.split('.')[0]

        cinit = None  # or self.readFile(cloud_init_file_path) # Kcontainer plugin support cloudinit initializzation
        sshk = None  # or self.readFile(pub key file path)       #

        ##### OTHER IMAGES USED
        # virt-cirros-0.3.4-x86_64-disk.img
        # cirros-0.3.5-x86_64-disk.img
        # ubuntu_container.tar.xz
        #####
        # br_name = str("br-%s" % net_uuid.split('-')[0])

        # creating the manifest for the container

        '''

        if gw:

            container_definition = {'name': container_name, 'uuid': container_uuid, 'base_image':'https://www.dropbox.com/s/7ko6orndmkkekc7/gateway.tar.gz', 'networks': [{'intf_name': 'wan' ,'br_name':'eno1'},{'intf_name': 'mgmt','br_name':br_name}], "user-data": cinit, "ssh-key": sshk}
            #container_definition = {'name': container_name, 'uuid': container_uuid, 'base_image':str('http://172.16.7.128/%s' % image_name), 'networks': [{'intf_name': 'wan' ,'br_name':'eno1'},{'intf_name': 'mgmt','br_name':br_name}], "user-data": cinit, "ssh-key": sshk}
        else:

            container_definition = {'name': container_name, 'uuid': container_uuid, 'base_image':'https://www.dropbox.com/s/53fp1u3jmxjmj6a/brain.tar.gz', 'networks': [{'intf_name': 'mgmt','br_name':br_name}], "user-data": cinit, "ssh-key": sshk}
            #container_definition = {'name': container_name, 'uuid': container_uuid, 'base_image':str('http://172.16.7.128/%s' % image_name), 'networks': [{'intf_name': 'mgmt','br_name':br_name}], "user-data": cinit, "ssh-key": sshk}
        '''
        entity_definition = {'status': 'define', 'name': container_name, 'version': 1, 'entity_data': manifest}

        json_data = json.dumps(entity_definition)

        # print("Press enter to define a container")
        # input()

        # writing the manifest to the desidered store of the destination node
        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, lxd.get('uuid'), container_uuid))
        self.dstore.put(uri, json_data)

        # busy waiting for the container to state change
        while True:
            print("Waiting container defined...")
            time.sleep(1)
            # reading state from actual store
            uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, lxd.get('uuid'), container_uuid))
            container_info = json.loads(self.astore.get(uri))
            if container_info is not None and container_info.get("status") == "defined":
                break

        # using a dput (delta put) to only update the container state, so cause a state transition
        uri = str(
            'dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (node_uuid, lxd.get('uuid'), container_uuid))
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
            print("Plugin was not loaded")
            exit()
        else:
            lxd = search[0]

        # print("Press enter to stop container")
        # input()

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

        uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, lxd.get('uuid'), container_uuid))
        self.dstore.remove(uri)

    def create_network(self, node_uuid, net_id, master=True):
        time.sleep(1)
        val = {'plugins': [{'name': 'brctl', 'version': 1, 'uuid': '',
                            'type': 'network', 'status': 'add'}]}
        uri = str('dfos://<sys-id>/%s/plugins' % node_uuid)
        self.dstore.dput(uri, json.dumps(val))
        time.sleep(4)

        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')
        print(all_plugins)
        nws = [x for x in all_plugins if x.get('type') == 'network']
        print(nws)
        print("locating brctl plugin")
        search = [x for x in nws if 'brctl' in x.get('name')]
        print(search)
        if len(search) == 0:
            print("Plugin was not loaded")
            exit()
        else:
            brctl = search[0]

        if master:
            net_data = {'status':'add', 'name': 'test', 'uuid': net_id, 'ip_range': '192.168.128.0/24', 'has_dhcp':True}
        else:
            net_data = {'status':'add', 'name': 'test', 'uuid': net_id}

        json_data = json.dumps(net_data)
        uri = str('dfos://<sys-id>/%s/network/%s/networks/%s' %
                  (node_uuid, brctl.get('uuid'), net_id))
        self.dstore.put(uri, json_data)

    def delete_network(self, node_uuid, net_id):
        time.sleep(1)

        uri = str('afos://<sys-id>/%s/plugins' % node_uuid)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')
        nws = [x for x in all_plugins if x.get('type') == 'network']
        print("locating brctl plugin")
        search = [x for x in nws if 'brctl' in x.get('name')]
        print(search)
        if len(search) == 0:
            print("Plugin was not loaded")
            exit(0)
        else:
            brctl = search[0]

        uri = str('dfos://<sys-id>/%s/network/%s/networks/%s#status=remove' % (node_uuid, brctl.get('uuid'), net_id))
        self.dstore.dput(uri)

    def main(self):

        uri = str('afos://<sys-id>/*/')
        self.astore.observe(uri, self.nodeDiscovered)

        vm_uuid = str(uuid.uuid4())

        while len(self.nodes) < 2:
            time.sleep(2)

        self.show_nodes()

        net_uuid = str(uuid.uuid4())

        vm_src_node = self.nodes.get(1)
        if vm_src_node is not None:
            vm_src_node = list(vm_src_node.keys())[0]

        vm_dst_node = self.nodes.get(2)
        if vm_dst_node is not None:
            vm_dst_node = list(vm_dst_node.keys())[0]

        input("Press enter to create network [vxlan]")

        self.create_network(vm_src_node, net_uuid, False)
        self.create_network(vm_dst_node, net_uuid, False)

        c_uuid = str(uuid.uuid4())
        c2_uuid = str(uuid.uuid4())
        vm_uuid = str(uuid.uuid4())
        vm2_uuid = str(uuid.uuid4())

        br_name = str("br-%s" % net_uuid.split('-')[0])


        gw_manifest = {'name': 'gw', 'uuid': c_uuid,
                       'base_image': 'https://www.dropbox.com/s/7ko6orndmkkekc7/gateway.tar.gz',
                       'networks': [{'intf_name': 'wan', 'br_name': 'ens33'},
                                    {'intf_name': 'mgmt', 'network_uuid': net_uuid}],
                       "user-data": None, "ssh-key": None}

        brain_manifest = {'name': 'brain', 'uuid': c2_uuid,
                          'base_image': 'https://www.dropbox.com/s/6eoaqhoknp7134t/brain.tar.gz',
                          'networks': [{'intf_name': 'mgmt', 'network_uuid': net_uuid}], "user-data": None, "ssh-key": None}

        input("Press enter to create vms")
        self.container_deploy(vm_src_node, c_uuid, gw_manifest)
        self.container_deploy(vm_src_node, c2_uuid, brain_manifest)
        self.vm_deploy(vm_src_node, vm_uuid, net_uuid)
        self.vm_deploy(vm_dst_node, vm2_uuid, net_uuid)

        input("press enter to destroy vms")
        self.vm_destroy(vm_dst_node, vm2_uuid)
        self.vm_destroy(vm_src_node, vm_uuid)
        self.container_destroy(vm_src_node, c2_uuid)
        self.container_destroy(vm_src_node, c_uuid)


        #self.migrate_vm(vm_src_node, vm_dst_node, vm_uuid)

        input("press enter to destroy vxlan")

        self.delete_network(vm_src_node, net_uuid)
        self.delete_network(vm_dst_node, net_uuid)

        input("press enter to exit")

        exit(0)


if __name__ == '__main__':
    c = Controll()
    c.main()
