import sys
import os
import uuid
import struct
import json
sys.path.append(os.path.join(sys.path[0], 'interfaces'))
from NetworkPlugin import *
from socket import *


class brctl(NetworkPlugin):

    def __init__(self, name, version, agent):
        super(brctl, self).__init__(version)
        self.name = name
        self.agent = agent
        self.interfaces_map = {}
        self.brmap = {}
        self.netmap = {}

    def createVirtualInterface(self, name, uuid):
        #sudo ip link add type veth
        #sudo ip link set dev veth1 addr 00:01:02:aa:bb:cc name vnic0
        #sudo ip link add name vnic0 type veth peer name vnic0-vm

        cmd = str('sudo ip link add name %s type veth peer name %-guest' % (name, name))
        self.agent.getOSPlugin().executeCommand(cmd)
        intf_uuid = uuid
        self.interfaces_map.update({uuid: name})

        return name, intf_uuid

    def creareVirtualBridge(self, name, uuid):
        cmd = str('sudo brctl addbr %s', name)
        self.agent.getOSPlugin().executeCommand(cmd)
        br_uuid = uuid
        self.brmap.update({br_uuid, name})
        return br_uuid, name

    def createVirtualNetwork(self, network_name, uuid, ip_range=None, has_dhcp=False, gateway=None):
        brcmd = str('sudo brctl addbr %s-net', network_name)
        net_uuid = uuid

        #

        self.agent.getOSPlugin().executeCommand(brcmd)

        if has_dhcp is True:
            address = self.cird2block(ip_range)
            dhcpq_cmd = str('sudo dnsmasq -d  --interface=%s-net --bind-interfaces  --dhcp-range=%s,'
                            '%s >/opt/fog/dhcp_out/%s.out 2>&1 & echo $! > /opt/fog/dhcp_out/%s.pid' %
                            (network_name, address[0], address[1], network_name, network_name))
            self.agent.getOSPlugin().executeCommand(dhcpq_cmd)

        self.netmap.update({net_uuid: {'network_name': network_name, 'intf': []}})

        return network_name, net_uuid

    def allocateBandwidth(self, intf_uuid, bandwidth):
        raise NotImplemented

    def assignInterfaceToNetwork(self, network_uuid, intf_uuid):
        raise NotImplemented

    def deleteVirtualInterface(self, intf_uuid):
        raise NotImplemented

    def deleteVirtualBridge(self, br_uuid):
        raise NotImplemented

    def removeInterfaceFromNetwork(self, network_uuid, intf_uuid):
        raise NotImplemented

    def deleteVirtualNetwork(self, network_uuid):
        raise NotImplemented

    def cird2block(self, cird):
        (ip, cidr) = cird.split('/')
        cidr = int(cidr)
        host_bits = 32 - cidr
        i = struct.unpack('>I', socket.inet_aton(ip))[0]
        start = (i >> host_bits) << host_bits
        end = i | ((1 << host_bits) - 1)

        return inet_ntoa(struct.pack('>I', start+1)), inet_ntoa(struct.pack('>I', end-1))

        #print (socket.inet_ntoa(struct.pack('>I',start+1)))
        #print (socket.inet_ntoa(struct.pack('>I',end-1)))


    def reactToCache(self, key, value):
        uuid = key.split('/')[-1]
        value = json.loads(value)
        action = value.get('status')
        entity_data = value.get('entity_data')
        react_func = self.react(action)
        if react_func is not None and entity_data is None:
            react_func(uuid)
        elif react_func is not None:
            entity_data.update({'entity_uuid': uuid})
            if action == 'define':
                react_func(**entity_data)
            else:
                react_func(entity_data)


    def react(self, action):
        r = {
            'define_interface': self.createVirtualInterface,
            'define_network': self.createVirtualNetwork,
            'define_bridge': self.creareVirtualBridge,
            'delete': self.deleteVirtualInterface,
            'interface_to_network': self.assignInterfaceToNetwork,
            'remove_interface': self.removeInterfaceFromNetwork,
        }

        return r.get(action, None)


