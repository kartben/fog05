import sys
import os
from fog05.interfaces.States import State

class Entity(object):

    def __init__(self):
        self.state=State.UNDEFINED
        self.uuid=""
        self.name=""
        self.instances=[]


    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def on_configured(self, configuration):
        raise NotImplementedError("This is and interface!")

    def on_clean(self):
        raise NotImplementedError("This is and interface!")

    def on_start(self):
        raise NotImplementedError("This is and interface!")

    def on_stop(self):
        raise NotImplementedError("This is and interface!")

    def on_pause(self):
        raise NotImplementedError("This is and interface!")

    def on_resume(self):
        raise NotImplementedError("This is and interface!")

    def before_migrate(self):
        raise NotImplementedError("This is and interface!")

    def after_migrate(self):
        raise NotImplementedError("This is and interface!")

    def add_instance(self, instance_uuid):
        if instance_uuid not in self.instances:
            self.instances.append(instance_uuid)

    def remove_instance(self, instance_uuid):
        if instance_uuid in self.instances:
            self.instances.remove(instance_uuid)