import sys
import os
import uuid
import struct
import json
from fog05.interfaces.NetworkPlugin import *
from jinja2 import Environment
import socket


class brctl(NetworkPlugin):

    def __init__(self, name, version, agent):
        super(brctl, self).__init__(version)
        self.name = name
        self.agent = agent
        self.interfaces_map = {}
        self.brmap = {}
        self.netmap = {}
        self.agent.logger.info('__init__()', ' Hello from bridge-utils Plugin')
        self.BASE_DIR = "/opt/fos/brctl"
        self.DHCP_DIR = "dhcp"
        self.HOME = str("network/%s/" % self.uuid)

        if not self.agent.getOSPlugin().dirExists(self.BASE_DIR):
            if not self.agent.getOSPlugin().dirExists(str("%s/%s") % (self.BASE_DIR, self.DHCP_DIR)):
                self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.DHCP_DIR))
        else:
            self.agent.getOSPlugin().createDir(str("%s") % self.BASE_DIR)
            self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.DHCP_DIR))

        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))
        self.agent.logger.info('startRuntime()', ' bridge-utils Plugin - Observing %s' % uri)
        self.agent.dstore.observe(uri, self.__react_to_cache)


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

    def createVirtualNetwork(self, network_name, net_uuid, ip_range=None, has_dhcp=False, gateway=None):

        net = self.netmap.get(net_uuid, None)
        if net is not None:
            raise NetworkAlreadyExistsException("%s network already exists" % net_uuid)

        #brcmd = str('sudo brctl addbr %s-net', network_name)
        #net_uuid = uuid
        #
        br_name = str("br%s" % net_uuid.split('-')[0])
        vxlan_file = self.__generate_vxlan_script(net_uuid)
        self.agent.getOSPlugin().executeCommand(vxlan_file, True)

        #self.agent.getOSPlugin().executeCommand(brcmd)

        if has_dhcp is True:
            address = self.__cird2block(ip_range)

            ifcmd = str('sudo ifconfig %s %s netmask %s' % (br_name, address[0], address[3]))
            dhcpq_cmd = str('sudo dnsmasq -d  --interface=%s --bind-interfaces  --dhcp-range=%s,'
                            '%s > %s/%s/%s.out 2>&1 & echo $! > %s/%s/%s.pid' %
                            (br_name, address[1], address[2], self.BASE_DIR, self.DHCP_DIR, br_name, self.BASE_DIR,
                             self.DHCP_DIR, br_name))

            self.agent.getOSPlugin().executeCommand(ifcmd, True)
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
        '''
            Convert cird subnet to first address (for router), dhcp avaiable range, netmask

        :param cird:
        :return:
        '''
        (ip, cidr) = cird.split('/')
        cidr = int(cidr)
        host_bits = 32 - cidr
        netmask = socket.inet_ntoa(struct.pack('!I', (1 << 32) - (1 << host_bits)))
        i = struct.unpack('>I', socket.inet_aton(ip))[0]
        start = (i >> host_bits) << host_bits
        end = i | ((1 << host_bits) - 1)

        return socket.inet_ntoa(struct.pack('>I', start + 1)), socket.inet_ntoa(
            struct.pack('>I', start + 2)), socket.inet_ntoa(struct.pack('>I', end - 1)),netmask

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

    def __generate_vxlan_script(self, net_uuid):
        template_sh = self.agent.getOSPlugin().readFile(os.path.join(sys.path[0], 'plugins', self.name,
                                                                      'templates', 'vxlan_creation.sh'))
        net_sh = Environment().from_string(template_sh)
        br_name = str("br%s" % net_uuid.split('-')[0])
        vxlan_name = str("vxl%s" % net_uuid.split('-')[0])
        vxlan_id = len(self.netmap)+1
        mcast_addr = str("239.0.0.%d" % vxlan_id)


        net_sh = net_sh.render(bridge_name=br_name, vxlan_intf_name=vxlan_name,
                                group_id=vxlan_id, mcast_group_address=mcast_addr)
        self.agent.getOSPlugin().storeFile(net_sh, self.BASE_DIR, str("%s.sh" % net_uuid.split('-')[0]))
        chmod_cmd = str("chmod +x %s/%s" % (self.BASE_DIR, str("%s.sh" % net_uuid.split('-')[0])))
        self.agent.getOSPlugin().executeCommand(chmod_cmd, True)

        return str("%s.sh" % net_uuid.split('-')[0])
