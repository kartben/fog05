import sys
import os
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from fog05.interfaces.States import State
from fog05.interfaces.Entity import Entity
from jinja2 import Environment
import json

class XENLibvirtEntity(Entity):

    def __init__(self, uuid, name, image_id, flavor_id):  # , cpu, ram, disk_size, networks, image, user_file, ssh_key):

        super(XENLibvirtEntity, self).__init__()
        self.uuid = uuid
        self.name = name
        self.image_id = image_id
        self.flavor_id = flavor_id

        self.user_file = None
        self.ssh_key = None
        self.networks = []

    def set_user_file(self, user_file):
        self.user_file = user_file

    def set_ssh_key(self, ssh_key):
        self.ssh_key = ssh_key

    def set_networks(self, networks):
        self.networks = networks

    def on_defined(self):
        self.state = State.DEFINED

