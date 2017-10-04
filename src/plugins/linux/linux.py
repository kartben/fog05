import sys
import os
import uuid
import psutil
sys.path.append(os.path.join(sys.path[0], 'interfaces'))
from States import State
from OSPlugin import *
from jinja2 import Environment
from subprocess import PIPE
import re
import platform
import netifaces
from socket import *

#platform.linux_distribution()



'''
        Redhat and friends: Test for /etc/redhat-release, check contents
        Debian: Test for /etc/debian_version, check contents
        Mandriva and friends: Test for /etc/version, check contents
        Slackware: Test for /etc/slackware-version, check contents

'''

class Linux(OSPlugin):

    def __init__(self, name, version):
        super(Linux, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name

    def executeCommand(self, command):
        print(command)
        cmd_splitted = command.split()
        p = psutil.Popen(cmd_splitted, stdout=PIPE)
        for line in p.stdout:
            print (line)

    def storeFile(self, content, file_path, filename):
        full_path = os.path.join(file_path, filename)
        f = open(full_path, 'w')
        f.write(content)
        f.flush()
        f.close()

    def readFile(self, file_path):
        with open(file_path,'r') as f:
            data = f.read()
        return data

    def getCPULevel(self):
        return psutil.cpu_percent(interval=1)

    def getMemoryLevel(self):
        return psutil.virtual_memory().percent

    def getStorageLevel(self):
        return psutil.disk_usage('/').percent

    def checkIfPidExists(self, pid):
        return psutil.pid_exsists(pid)

    def sendSignal(self, signal, pid):
        if self.checkIfPidExists(pid) is False:
            raise ProcessNotExistingException("Process %d not exists" % pid)
        else:
            psutil.Process(pid).send_signal(signal)
        return True

    def sendSigInt(self, pid):
        if self.checkIfPidExists(pid) is False:
            raise ProcessNotExistingException("Process %d not exists" % pid)
        else:
            psutil.Process(pid).send_signal(2)
        return True

    def sendSigKill(self, pid):
        if self.checkIfPidExists(pid) is False:
            raise ProcessNotExistingException("Process %d not exists" % pid)
        else:
            psutil.Process(pid).send_signal(9)
        return True

    def getNetworkLevel(self):
        raise NotImplementedError

    def installPackage(self, packages):
        raise NotImplementedError

    def removePackage(self, packages):
        raise NotImplementedError

    def getPid(self,process):
        raise NotImplementedError

    def getProcessorInformation(self):
        cpu=[]
        for i in range(0, psutil.cpu_count(logical=False)):
            model = self.get_processor_name()
            frequency = psutil.cpu_freq(percpu=True)
            if len(frequency) == 0:
                frequency = self.get_frequency_from_cpuinfo()
            else:
                frequency = frequency[i][2]
            arch = platform.machine()
            cpu.append({'model': model, 'frequency': frequency, 'arch': arch})
        return cpu

    def getMemoryInformation(self):
        #conversion to MB
        return {'size': psutil.virtual_memory()[0]/1024/1024}

    def getDisksInformation(self):
        disks=[]
        for d in psutil.disk_partitions():
            dev = d[0]
            mount = d[1]
            dim = psutil.disk_usage(mount)[0]/1024/1024/1024 #conversion to gb
            fs = d[2]
            disks.append({'local_address': dev, 'dimension': dim, 'mount_point': mount, 'filesystem': fs})
        return disks

    def getIOInformations(self):
        raise NotImplemented

    def getAcceleratorsInformations(self):
        raise NotImplemented

    def getNetworkInformations(self):
        #{'default': {2: ('172.16.0.1', 'brq2376512c-13')}, 2: [('10.0.0.1', 'eno4', True), ('172.16.0.1', 'brq2376512c-13', True), ('172.16.1.1', 'brqf110e342-9b', False), ('10.0.0.1', 'eno4', False)]}

        nets=[]
        intfs = psutil.net_if_stats().keys()
        gws = netifaces.gateways().get(2)
        for k in intfs:
            intf_info=psutil.net_if_addrs().get(k)

            ipv4_info = [x for x in intf_info if x[0] == AddressFamily.AF_INET]
            ipv6_info = [x for x in intf_info if x[0] == AddressFamily.AF_INET6]
            l2_info = [x for x in intf_info if x[0] == AddressFamily.AF_PACKET]

            if len(ipv4_info) > 0:
                ipv4_info=ipv4_info[0]
                ipv4 = ipv4_info[1]
                ipv4mask = ipv4_info[2]
                search_gw = [x[0] for x in gws if x[1] == k]
                if len(search_gw) > 0:
                    ipv4gateway = search_gw[0]
                else:
                    ipv4gateway = ''

            else:
                ipv4 = ''
                ipv4gateway = ''
                ipv4mask = ''

            if len(ipv6_info) > 0:
                ipv6_info = ipv6_info[0]
                ipv6 = ipv6_info[1]
                ipv6mask = ipv6_info[2]
            else:
                ipv6 = ''
                ipv6mask = ''

            if len(l2_info) > 0:
                l2_info = l2_info[0]
                mac = l2_info[1]
            else:
                mac = ''

            speed = psutil.net_if_stats().get(k)[2]
            inft_conf = {'ipv4_address': ipv4, 'ipv4_netmask': ipv4mask, "ipv4_gateway":ipv4gateway, "ipv6_address":
                ipv6, 'ipv6_netmask': ipv6mask}


            nets.append({'intf_name': k, 'inft_configuration': inft_conf, 'intf_mac_address': mac,  'intf_speed':
                speed })

        return nets




    def getPositionInformation(self):
        raise NotImplemented


    def get_processor_name(self):
        command = "cat /proc/cpuinfo".split()
        p = psutil.Popen(command, stdout=PIPE)
        for line in p.stdout:
            line = line.decode()
            if "model name" in line:
                    return re.sub(".*model name.*:", "", line, 1)
        return ""

    def get_frequency_from_cpuinfo(self):
        command = "cat /proc/cpuinfo".split()
        p = psutil.Popen(command, stdout=PIPE)
        for line in p.stdout:
            line = line.decode()
            if "cpu MHz" in line:
                    return float(re.sub(".*cpu MHz.*:", "", line, 1))
        return 0.0