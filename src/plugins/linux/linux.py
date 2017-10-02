import sys
import os
import uuid
import psutil
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from States import State
from OSPlugin import *
from jinja2 import Environment
from subprocess import PIPE

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