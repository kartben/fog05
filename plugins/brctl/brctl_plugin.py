import sys
import os
import uuid
import struct
import json
from fog05.interfaces.NetworkPlugin import *
from jinja2 import Environment
import socket


class brctl(NetworkPlugin):

    def __init__(self, name, version, agent, plugin_uuid):
        super(brctl, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.interfaces_map = {}
        self.brmap = {}
        self.netmap = {}
        self.agent.logger.info('__init__()', ' Hello from bridge-utils Plugin')
        self.BASE_DIR = "/opt/fos/brctl"
        self.DHCP_DIR = "dhcp"
        self.HOME = str("network/%s" % self.uuid)
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)

        if self.agent.getOSPlugin().dirExists(self.BASE_DIR):
            if not self.agent.getOSPlugin().dirExists(str("%s/%s") % (self.BASE_DIR, self.DHCP_DIR)):
                self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.DHCP_DIR))
        else:
            self.agent.getOSPlugin().createDir(str("%s") % self.BASE_DIR)
            self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.DHCP_DIR))


        '''
        should listen on:
        
        - dfos://<sys-id>/<node-id>/network/<myuuid>/networks/*
        - dfos://<sys-id>/<node-id>/network/<myuuid>/bridges/*
        - dfos://<sys-id>/<node-id>/network/<myuuid>/interfaces/*
        
        '''

        uri = str('%s/%s/networks/*' % (self.agent.dhome, self.HOME))
        self.agent.dstore.observe(uri, self.__react_to_cache_networks)
        self.agent.logger.info('startRuntime()', ' bridge-utils Plugin - Observing %s' % uri)



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

    def createVirtualNetwork(self, network_name, net_uuid, ip_range=None, has_dhcp=False, gateway=None, manifest=None):

        net = self.netmap.get(net_uuid, None)
        if net is not None:
            raise NetworkAlreadyExistsException("%s network already exists" % net_uuid)

        info = {}
        pi = []

        info.update({'name': network_name})
        info.update({'interfaces': pi})
        info.update({'uuid': net_uuid})
        info.update({'has_dhcp': has_dhcp})
        info.update({'ip_range': ip_range})
        info.update({'gateway': gateway})
        #brcmd = str('sudo brctl addbr %s-net', network_name)
        #net_uuid = uuid
        #
        br_name = str("br-%s" % net_uuid.split('-')[0])

        vxlan_file, vxlan_dev, vxlan_id, vxlan_mcast = self.__generate_vxlan_script(net_uuid, manifest)
        self.agent.getOSPlugin().executeCommand(str("%s/%s" % (self.BASE_DIR, vxlan_file)), True)

        info.update({'virtual_device': br_name})
        info.update({'vxlan_dev': vxlan_dev})
        info.update({'vxlan_id': vxlan_id})
        info.update({'multicast_address': vxlan_mcast})




        #self.agent.getOSPlugin().executeCommand(brcmd)

        if has_dhcp is True:
            address = self.__cird2block(ip_range)

            ifcmd = str('sudo ifconfig %s %s netmask %s' % (br_name, address[0], address[3]))
            #dhcpq_cmd = str('sudo dnsmasq -d  --interface=%s --bind-interfaces  --dhcp-range=%s,'
            #                '%s --listen-address %s > %s/%s/%s.out 2>&1 & echo $! > %s/%s/%s.pid' %
            #                (br_name, address[1], address[2], address[0], self.BASE_DIR, self.DHCP_DIR, br_name,
            #                 self.BASE_DIR,
            #                 self.DHCP_DIR, br_name))
            file_name = str("%s_dnsmasq.pid" % br_name)
            pid_file_path = str("%s/%s/%s" % (self.BASE_DIR, self.DHCP_DIR, file_name))

            dhcp_cmd = self.__generate_dnsmaq_script(br_name, address[1], address[2], address[0],pid_file_path)
            dhcp_cmd = str("%s/%s/%s" % (self.BASE_DIR, self.DHCP_DIR, dhcp_cmd))

            self.agent.getOSPlugin().executeCommand(ifcmd, True)
            self.agent.getOSPlugin().executeCommand(dhcp_cmd)

        self.netmap.update({net_uuid: info})

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
        if len(net.get('interfaces')) > 0:
            raise NetworkHasPendingInterfacesException("%s has pending interfaces" % network_uuid)

        shutdown_file = self.__generate_vxlan_shutdown_script(network_uuid)
        shutdown_file = str("%s/%s" % (self.BASE_DIR, shutdown_file))
        start_file = str("%s/%s" % (self.BASE_DIR, str("%s.sh" % network_uuid.split('-')[0])))
        dnsmasq_file = str("%s/%s/%s" % (self.BASE_DIR, self.DHCP_DIR,
                                         str("br-%s_dnsmasq.sh" % network_uuid.split('-')[0])))
        self.agent.getOSPlugin().executeCommand(shutdown_file)

        self.agent.getOSPlugin().removeFile(shutdown_file)
        self.agent.getOSPlugin().removeFile(start_file)
        self.agent.getOSPlugin().removeFile(dnsmasq_file)

        self.netmap.pop(network_uuid)

        return True

    def stopNetwork(self):
        keys = list(self.netmap.keys())
        for k in keys:
            self.deleteVirtualNetwork(k)
        return True

    def getNetworkInfo(self, network_uuid):
        if network_uuid is None:
            return self.netmap
        return self.netmap.get(network_uuid)

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

    def __react_to_cache_networks(self, key, value, v):
        self.agent.logger.info('__react_to_cache_networks()',
                               ' BRCTL Plugin - React to to URI: %s Value: %s Version: %s' % (key, value, v))
        uuid = key.split('/')[-1]
        value = json.loads(value)
        action = value.get('status')
        react_func = self.__react(action)
        if react_func is not None: # and value is None:
            react_func(**value)
        #elif react_func is not None:
        #    value.update({'uuid': uuid})
        #    if action == 'define':
        #        react_func(**value)
        #    else:
        #        react_func(value)

    def __parse_manifest_for_add(self, **kwargs):
        net_uuid = kwargs.get('uuid')
        name = kwargs.get('name')
        ip_range = kwargs.get('ip_range')
        has_dhcp = kwargs.get('has_dhcp')
        gw = kwargs.get('gateway')
        manifest = kwargs
        self.createVirtualNetwork(name, net_uuid, ip_range, has_dhcp, gw, manifest)

    def __parse_manifest_for_remove(self, **kwargs):
        net_uuid = kwargs.get('uuid')
        self.deleteVirtualNetwork(net_uuid)

    def __react(self, action):
        r = {
            'add': self.__parse_manifest_for_add,
            'remove': self.__parse_manifest_for_remove,
        }

        return r.get(action, None)

    def __generate_vxlan_shutdown_script(self, net_uuid):
        template_sh = self.agent.getOSPlugin().readFile(os.path.join(self.DIR, 'templates', 'vxlan_destroy.sh'))
        br_name = str("br-%s" % net_uuid.split('-')[0])
        vxlan_name = str("vxl-%s" % net_uuid.split('-')[0])
        file_name = str("%s_dnsmasq.pid" % br_name)
        pid_file_path = str("%s/%s/%s" % (self.BASE_DIR, self.DHCP_DIR, file_name))

        net_sh = Environment().from_string(template_sh)
        net_sh = net_sh.render(bridge=br_name, vxlan_intf_name=vxlan_name, dnsmasq_pid_file=pid_file_path)
        file_name = str("%s_stop.sh" % br_name)
        self.agent.getOSPlugin().storeFile(net_sh, self.BASE_DIR, file_name)
        chmod_cmd = str("chmod +x %s/%s" % (self.BASE_DIR, file_name))
        self.agent.getOSPlugin().executeCommand(chmod_cmd, True)

        return file_name

    def __generate_dnsmaq_script(self, br_name, start_addr, end_addr, listen_addr, pid_file):
        template_sh = self.agent.getOSPlugin().readFile(os.path.join(self.DIR, 'templates', 'dnsmasq.sh'))
        dnsmasq_sh = Environment().from_string(template_sh)
        dnsmasq_sh = dnsmasq_sh.render(bridge_name=br_name, dhcp_start=start_addr,
                                dhcp_end=end_addr, listen_addr=listen_addr, pid_path=pid_file)
        file_name = str("%s_dnsmasq.sh" % br_name)
        path = str("%s/%s" % (self.BASE_DIR, self.DHCP_DIR))
        self.agent.getOSPlugin().storeFile(dnsmasq_sh, path, file_name)
        chmod_cmd = str("chmod +x %s/%s" % (path, file_name))
        self.agent.getOSPlugin().executeCommand(chmod_cmd, True)

        return file_name

    def __generate_vxlan_script(self, net_uuid, manifest=None):
        template_sh = self.agent.getOSPlugin().readFile(os.path.join(self.DIR, 'templates', 'vxlan_creation.sh'))
        net_sh = Environment().from_string(template_sh)
        br_name = str("br-%s" % net_uuid.split('-')[0])
        vxlan_name = str("vxl-%s" % net_uuid.split('-')[0])

        if manifest is not None:
            vxl_id_manifest = manifest.get('vxlan_id')
            if vxl_id_manifest is not None:
                vxlan_id = vxl_id_manifest
            else:
                vxlan_id = len(self.netmap) + 1
            vxl_mcast_manifest = manifest.get('multicast_address')
            if vxl_mcast_manifest is not None:
                mcast_addr = vxl_mcast_manifest
            else:
                mcast_addr = str("239.0.0.%d" % vxlan_id)
        else:
            vxlan_id = len(self.netmap) + 1
            mcast_addr = str("239.0.0.%d" % vxlan_id)

        net_sh = net_sh.render(bridge_name=br_name, vxlan_intf_name=vxlan_name,
                               group_id=vxlan_id, mcast_group_address=mcast_addr)
        self.agent.getOSPlugin().storeFile(net_sh, self.BASE_DIR, str("%s.sh" % net_uuid.split('-')[0]))
        chmod_cmd = str("chmod +x %s/%s" % (self.BASE_DIR, str("%s.sh" % net_uuid.split('-')[0])))
        self.agent.getOSPlugin().executeCommand(chmod_cmd, True)

        return str("%s.sh" % net_uuid.split('-')[0]), vxlan_name, vxlan_id, mcast_addr
