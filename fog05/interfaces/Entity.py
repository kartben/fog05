import sys
import os
from fog05.interfaces.States import State

class Entity(object):

    def __init__(self):
        self.state=State.UNDEFINED
        self.uuid=''
        self.name=''
        self.instances={}


    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def on_configured(self, configuration):
        raise NotImplementedError('This is and interface!')

    def on_clean(self):
        raise NotImplementedError('This is and interface!')

    def on_start(self):
        raise NotImplementedError('This is and interface!')

    def on_stop(self):
        raise NotImplementedError('This is and interface!')

    def on_pause(self):
        raise NotImplementedError('This is and interface!')

    def on_resume(self):
        raise NotImplementedError('This is and interface!')

    def before_migrate(self):
        raise NotImplementedError('This is and interface!')

    def after_migrate(self):
        raise NotImplementedError('This is and interface!')

    def has_instance(self, instance_uuid):
        return instance_uuid in self.instances.keys()

    def add_instance(self, instance_object):
        if instance_object.uuid not in self.instances.keys():
            self.instances.update({instance_object.uuid: instance_object})

    def remove_instance(self, instance_object):
        if instance_object.uuid in self.instances.keys():
            self.instances.pop(instance_object.uuid);

    def get_instance(self,instance_uuid):
        return self.instances.get(instance_uuid, None)
