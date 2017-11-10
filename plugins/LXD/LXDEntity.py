import sys
import os
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from fog05.interfaces.States import State
from fog05.interfaces.Entity import Entity

class LXDEntity(Entity):

    def __init__(self, uuid, name, networks, image, user_file, ssh_key, docker_file, profiles):

        super(LXDEntity, self).__init__()
        self.uuid = uuid
        self.name = name
        self.networks = networks
        self.image = image
        self.user_file = user_file
        self.ssh_key = ssh_key
        self.docker_file = docker_file
        self.profiles = profiles
        self.conf = None

    def onConfigured(self,configuration):
        self.conf = configuration
        self.state = State.CONFIGURED

    def onClean(self):
        self.state = State.DEFINED

    def onStart(self):
        self.state = State.RUNNING
    
    def onStop(self):
        self.state = State.CONFIGURED

    def onPause(self):
        self.state = State.PAUSED

    def onResume(self):
        self.state = State.RUNNING
