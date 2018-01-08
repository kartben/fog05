import sys
import os
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from fog05.interfaces.States import State
from fog05.interfaces.Entity import Entity
from jinja2 import Environment
import json

class KVMLibvirtEntity(Entity):

    def __init__(self, uuid, name, cpu, ram, disk, disk_size, cdrom, networks, image, user_file, ssh_key):

        super(KVMLibvirtEntity, self).__init__()
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

    def on_configured(self, configuration):
        self.xml = configuration
        self.state = State.CONFIGURED

    def on_clean(self):
        self.state = State.DEFINED

    def on_start(self):
        self.state = State.RUNNING
    
    def on_stop(self):
        self.state = State.CONFIGURED

    def on_pause(self):
        self.state = State.PAUSED

    def on_resume(self):
        self.state = State.RUNNING
