import sys
import os
from fog05.interfaces.States import State
from fog05.interfaces.Entity import Entity


class NativeEntity(Entity):
    def __init__(self, uuid, name, command, source, args, outfile):
        super(NativeEntity, self).__init__()
        self.uuid = uuid
        self.name = name
        self.command = command
        self.args = args
        self.outfile = outfile
        self.pid = -1
        self.source = source
        self.process = None


    def on_configured(self):
        self.state = State.CONFIGURED

    def on_clean(self):
        self.state = State.DEFINED

    def on_start(self, pid, process):
        self.pid = pid
        self.process = process
        self.state = State.RUNNING

    def on_stop(self):
        self.pid = -1
        self.process = None
        self.state = State.CONFIGURED

    def on_pause(self):
        self.state = State.PAUSED

    def on_resume(self):
        self.state = State.RUNNING

    def after_migrate(self):
        raise Exception("Cannot migrate Native")

    def before_migrate(self):
        raise Exception("Cannot migrate Native")
