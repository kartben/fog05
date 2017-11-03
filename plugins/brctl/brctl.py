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

        cmd = str('' % (name, name))
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
            address = self.__cird2block(ip_range)
            dhcpq_cmd = str('sudo dnsmasq -d  --interface=%s-net --bind-interfaces  --dhcp-range=%s,'
                            '%s >/opt/fog/dhcp_out/%s.out 2>&1 & echo $! > /opt/fog/dhcp_out/%s.pid' %
                            (network_name, address[0], address[1], network_name, network_name))
            self.agent.getOSPlugin().executeCommand(dhcpq_cmd)

        self.netmap.update({net_uuid: {'network_name': network_name, 'intf': []}})

        return network_name, net_uuid

    def allocateBandwidth(self, intf_uuid, bandwidth):
        raise NotImplemented

    def assignInterfaceToNetwork(self, network_uuid, intf_uuid):
        #brctl addif virbr0 vnet0
        intf = self.interfaces_map.get(intf_uuid, None)
        if intf is None:
            raise InterfaceNotExistingException("%s interface not exists" % intf_uuid)
        net = self.netmap.get(network_uuid, None)
        if net is None:
            raise BridgeAssociatedToNetworkException("%s network not exists" % network_uuid)

        br_cmd = str('sudo brctl addif %s-net %s' % (net.get('network_name'), intf))
        self.agent.getOSPlugin().executeCommand(br_cmd)

        return True

    def deleteVirtualInterface(self, intf_uuid):
        #ip link delete dev ${interface name}
        intf = self.interfaces_map.get(intf_uuid, None)
        if intf is None:
            raise InterfaceNotExistingException("%s interface not exists" % intf_uuid)
        rm_cmd = str("sudo ip link delete dev %s" % intf)
        self.agent.getOSPlugin().executeCommand(rm_cmd)
        self.interfaces_map.pop(intf_uuid)
        return True

    def deleteVirtualBridge(self, br_uuid):

        net = self.netmap.get(br_uuid, None)
        if net is not None:
            raise BridgeAssociatedToNetworkException("%s associated to a network" % br_uuid)
        br = self.brmap.get(br_uuid, None)
        if br is None:
            raise BridgeNotExistingException("%s bridge not exists" % br_uuid)

        rm_cmd = str("sudo brcrl delbr %s" % br)
        self.agent.getOSPlugin().executeCommand(rm_cmd)
        self.brmap.pop(br_uuid)
        return True



    def removeInterfaceFromNetwork(self, network_uuid, intf_uuid):
        net = self.netmap.get(network_uuid, None)
        if net is None:
            raise BridgeAssociatedToNetworkException("%s network not exists" % network_uuid)
        intf = self.brmap.get(intf_uuid, None)
        if intf is None:
            raise InterfaceNotExistingException("%s interface not exists" % intf_uuid)
        if intf not in net.get('intf'):
            raise InterfaceNotInNetworkException("%s interface not in this networks" % intf_uuid)

        net.get('intf').remove(intf)
        return True

    def deleteVirtualNetwork(self, network_uuid):
        net = self.netmap.get(network_uuid, None)
        if net is None:
            raise BridgeAssociatedToNetworkException("%s network not exists" % network_uuid)
        if len(net.get('intf')) > 0:
            raise NetworkHasPendingInterfacesException("%s has pending interfaces" % network_uuid)

        dhcp_pid_file = str('/opt/fog/dhcp_out/%s.pid' % net.get('network_name'))
        if self.agent.getOSPlugin().fileExists(dhcp_pid_file):
            pid = self.agent.getOSPlugin().read_file(dhcp_pid_file)
            self.agent.getOSPlugin().sendSigKill(pid)


        rm_cmd = str("sudo brcrl delbr %s-net" % net.get('network_name'))
        self.agent.getOSPlugin().executeCommand(rm_cmd)
        self.brmap.pop(network_uuid)


        return True

    def __cird2block(self, cird):
        (ip, cidr) = cird.split('/')
        cidr = int(cidr)
        host_bits = 32 - cidr
        i = struct.unpack('>I', socket.inet_aton(ip))[0]
        start = (i >> host_bits) << host_bits
        end = i | ((1 << host_bits) - 1)

        return inet_ntoa(struct.pack('>I', start+1)), inet_ntoa(struct.pack('>I', end-1))

    def __react_to_cache(self, key, value):
        uuid = key.split('/')[-1]
        value = json.loads(value)
        action = value.get('status')
        entity_data = value.get('entity_data')
        react_func = self.__react(action)
        if react_func is not None and entity_data is None:
            react_func(uuid)
        elif react_func is not None:
            entity_data.update({'entity_uuid': uuid})
            if action == 'define':
                react_func(**entity_data)
            else:
                react_func(entity_data)


    def __react(self, action):
        r = {
            'define_interface': self.createVirtualInterface,
            'define_network': self.createVirtualNetwork,
            'define_bridge': self.creareVirtualBridge,
            'delete': self.deleteVirtualInterface,
            'interface_to_network': self.assignInterfaceToNetwork,
            'remove_interface': self.removeInterfaceFromNetwork,
        }

        return r.get(action, None)


