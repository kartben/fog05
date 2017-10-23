import sys
import os
import uuid
import psutil

sys.path.append(os.path.join(sys.path[0], 'interfaces'))
from States import State
from OSPlugin import *
from jinja2 import Environment
from subprocess import PIPE
import subprocess
import re
import platform
import netifaces
from socket import *

# platform.linux_distribution()



'''
        Redhat and friends: Test for /etc/redhat-release, check contents
        Debian: Test for /etc/debian_version, check contents
        Mandriva and friends: Test for /etc/version, check contents
        Slackware: Test for /etc/slackware-version, check contents
        Ubuntu: test fot /etc/lsb-release, check contents

'''


class Linux(OSPlugin):
    def __init__(self, name, version):
        super(Linux, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name
        self.pm = None

        self.distro = self.__check_distro()
        if self.distro == "":
            print ("Linux distribution not recognized!")
        else:
            print ("Running on %s" % self.distro)
            self.pm = self.__get_package_manager(self.distro)
            print ("Package manager loaded! Name %s" % self.pm.name)

    def executeCommand(self, command, blocking=False):
        print(command)
        cmd_splitted = command.split()
        p = psutil.Popen(cmd_splitted, stdout=PIPE)
        if blocking:
            p.wait()

        for line in p.stdout:
            print (line)

    def addKnowHost(self, hostname, ip):
        add_cmd = str("sudo %s -a %s %s" % (os.path.join(sys.path[0], 'plugins', self.name, 'scripts',
                                                        'manage_hosts.sh'),
                                       hostname, ip))
        self.executeCommand(add_cmd, True)

    def removeKnowHost(self, hostname):
        del_cmd = str("sudo %s -d %s" % (os.path.join(sys.path[0], 'plugins', self.name, 'scripts', 'manage_hosts.sh'),
                                    hostname))
        self.executeCommand(del_cmd, True)

    def fileExists(self, file_path):
        return os.path.isfile(file_path)

    def storeFile(self, content, file_path, filename):
        full_path = os.path.join(file_path, filename)
        f = open(full_path, 'w')
        f.write(content)
        f.flush()
        f.close()

    def readFile(self, file_path, root=False):
        data = ""
        if root:
            file_path = str("sudo cat %s" % file_path)
            process = subprocess.Popen(file_path.split(), stdout=subprocess.PIPE)
            # read one line at a time, as it becomes available
            for line in iter(process.stdout.readline, ''):
                data = str(data + "%s" % line)
        else:
            with open(file_path, 'r') as f:
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
        self.pm.installPackage(packages)

    def removePackage(self, packages):
        self.pm.removePackage(packages)

    def getPid(self, process):
        raise NotImplementedError

    def getProcessorInformation(self):
        cpu = []
        for i in range(0, psutil.cpu_count(logical=False)):
            model = self.__get_processor_name()
            try:
                frequency = psutil.cpu_freq(percpu=True)
                if len(frequency) == 0:
                    frequency = self.__get_frequency_from_cpuinfo()
                else:
                    frequency = frequency[i][2]
            except AttributeError:
                frequency = self.__get_frequency_from_cpuinfo()
            arch = platform.machine()
            cpu.append({'model': model, 'frequency': frequency, 'arch': arch})
        return cpu

    def getMemoryInformation(self):
        # conversion to MB
        return {'size': psutil.virtual_memory()[0] / 1024 / 1024}

    def getDisksInformation(self):
        disks = []
        for d in psutil.disk_partitions():
            dev = d[0]
            mount = d[1]
            dim = psutil.disk_usage(mount)[0] / 1024 / 1024 / 1024  # conversion to gb
            fs = d[2]
            disks.append({'local_address': dev, 'dimension': dim, 'mount_point': mount, 'filesystem': fs})
        return disks

    def getIOInformations(self):
        raise NotImplemented

    def getAcceleratorsInformations(self):
        raise NotImplemented

    def getNetworkInformations(self):
        # {'default': {2: ('172.16.0.1', 'brq2376512c-13')}, 2: [('10.0.0.1', 'eno4', True), ('172.16.0.1', 'brq2376512c-13', True), ('172.16.1.1', 'brqf110e342-9b', False), ('10.0.0.1', 'eno4', False)]}

        nets = []
        intfs = psutil.net_if_stats().keys()
        gws = netifaces.gateways().get(2)
        for k in intfs:
            intf_info = psutil.net_if_addrs().get(k)

            ipv4_info = [x for x in intf_info if x[0] == AddressFamily.AF_INET]
            ipv6_info = [x for x in intf_info if x[0] == AddressFamily.AF_INET6]
            l2_info = [x for x in intf_info if x[0] == AddressFamily.AF_PACKET]

            if len(ipv4_info) > 0:
                ipv4_info = ipv4_info[0]
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
            inft_conf = {'ipv4_address': ipv4, 'ipv4_netmask': ipv4mask, "ipv4_gateway": ipv4gateway, "ipv6_address":
                ipv6, 'ipv6_netmask': ipv6mask}

            nets.append({'intf_name': k, 'inft_configuration': inft_conf, 'intf_mac_address': mac, 'intf_speed':
                speed})

        return nets

    def getUUID(self):
        # $ blkid / dev / sda1
        # /dev/sda1: LABEL = "/"  UUID = "ee7cf0a0-1922-401b-a1ae-6ec9261484c0" SEC_TYPE = "ext2" TYPE = "ext3"
        # generate uuid from this or from cpuid or mb uuid from /sys/class/dmi/id/product_uuid

        # p = psutil.Popen('cat /sys/class/dmi/id/product_uuid'.split(), stdout=PIPE) no need of regex
        p = psutil.Popen('sudo cat /sys/class/dmi/id/product_uuid'.split(), stdout=PIPE)
        res = ""
        for line in p.stdout:
            res = str(res + "%s" % line)
        return res.lower()
        '''
        uuid_regex = r"UUID=\"(.{0,37})\""
        p = psutil.Popen('sudo blkid /dev/sda1'.split(), stdout=PIPE)
        res = ""
        for line in p.stdout:
            res = str(res+"%s" % line)
        m = re.search(uuid_regex, res)
        if m:
            found = m.group(1)
        return found
        '''

    def getHostname(self):
        res = ''
        p = psutil.Popen('hostname', stdout=PIPE)
        for line in p.stdout:
            line = line.decode()
            res = str(res + "%s" % line)
        return res.strip()

    def getPositionInformation(self):
        raise NotImplemented

    def __get_processor_name(self):
        command = "cat /proc/cpuinfo".split()
        p = psutil.Popen(command, stdout=PIPE)
        for line in p.stdout:
            line = line.decode()
            if "model name" in line:
                return re.sub(".*model name.*:", "", line, 1)
        return ""

    def __get_frequency_from_cpuinfo(self):
        command = "cat /proc/cpuinfo".split()
        p = psutil.Popen(command, stdout=PIPE)
        for line in p.stdout:
            line = line.decode()
            if "cpu MHz" in line:
                return float(re.sub(".*cpu MHz.*:", "", line, 1))
        return 0.0

    def __check_distro(self):

        lsb = "/etc/lsb-release"
        deb = "/etc/debian_version"
        rh = "/etc/redhat-release"
        sw = "/etc/slackware-release"
        go = "/etc/gentoo-release"

        if os.path.exists(deb):
            if os.path.exists(lsb):
                return "ubuntu"
            else:
                return "debian"
        elif os.path.exists(rh):
            return "redhat"
        elif os.path.exists(sw):
            return "slackware"
        elif os.path.exists(go):
            return "gentoo"
        else:
            return ""

    def __get_package_manager(self, distro):
        '''
        From distribution name to package manager wrapper
        :param distro: Linux distribution name
        :return: a wrapper for basic operation on package manager
        '''

        wr = {
            'debian': self.AptWrapper(),
            'ubuntu': self.AptWrapper(),
            'redhat': self.YumWrapper()
        }

        return wr.get(distro, None)

    class AptWrapper(object):
        def __init__(self):
            self.name = "apt"

        def update_packages(self):
            cmd = "sudo apt update && sudo apt upgrade -y && sudo apt autoremove --purge"
            os.system(cmd)

        def install_package(self, pkg_name):
            cmd = str("sudo apt update && sudo apt install %s" % pkg_name)
            os.system(cmd)

        def remove_package(self, pkg_name):
            cmd = str("sudo apt update && sudo apt remove %s" % pkg_name)
            os.system(cmd)

        def purge_package(self, pkg_name):
            cmd = str("sudo apt update && sudo apt purge %s" % pkg_name)
            os.system(cmd)


    class YumWrapper(object):
        def __init__(self):
            self.name = "yum"

        def update_packages(self):
            cmd = "sudo yum update -y && sudo yum autoremove"
            os.system(cmd)

        def install_package(self, pkg_name):
            cmd = str("sudo yum install %s" % pkg_name)
            os.system(cmd)

        def remove_package(self, pkg_name):
            cmd = str("sudo yum remove %s" % pkg_name)
            os.system(cmd)

        def purge_package(self, pkg_name):
            cmd = str("sudo yum remove %s" % pkg_name)
            os.system(cmd)
