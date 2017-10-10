import sys
import os
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from States import State
from Entity import Entity
from jinja2 import Environment

class LibVirtEntity(Entity):

    def __init__(self, uuid, name, cpu, ram, disk, disk_size, cdrom, networks, image, user_file, ssh_key):

        super(LibVirtEntity, self).__init__()
        self.uuid = uuid
        self.name = name
        self.cpu = cpu
        self.ram = ram
        self.disk = disk
        self.disk_size = disk_size
        self.cdrom = cdrom
        self.networks = networks
        self.image = image
        self.user_file = user_file
        self.ssh_key = ssh_key

    def onConfigured(self,configuration):
        self.xml = configuration
        self.state = State.CONFIGURED

    def onClean(self):
        self.state =  State.DEFINED

    def onStart(self):
        self.state = State.RUNNING
    
    def onStop(self):
        self.state = State.CONFIGURED

    def onPause(self):
        self.state = State.PAUSED

    def onResume(self):
        self.state = State.RUNNING
