import sys
import os
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from States import State

class Entity(object):

    def __init__(self):
        self.state=State.UNDEFINED
        self.uuid=""
        self.name=""

    def getState(self):
        return self.state

    def setState(self,state):
        self.state = state

    def onConfigured(self, configuration):
        raise NotImplementedError("This is and interface!")

    def onClean(self):
        raise NotImplementedError("This is and interface!")

    def onStart(self):
        raise NotImplementedError("This is and interface!")

    def onStop(self):
        raise NotImplementedError("This is and interface!")

    def onPause(self):
        raise NotImplementedError("This is and interface!")

    def onResume(self):
        raise NotImplementedError("This is and interface!")

    def beforeMigrate(self):
        raise NotImplementedError("This is and interface!")

    def afterMigrate(self):
        raise NotImplementedError("This is and interface!")