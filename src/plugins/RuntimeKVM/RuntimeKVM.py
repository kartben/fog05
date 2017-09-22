import sys
sys.path.append('/Users/gabri/Workspace/FogOS/src/')
from interfaces.RuntimePlugin import RuntimePlugin

class RuntimeKVM(RuntimePlugin):

    def __init__(self):
        self.uuid='kvm'

    def startRuntime(self):
        print('KVM Started!\n')