import sys
import os
import uuid
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from RuntimePlugin import RuntimePlugin

class RuntimeLibVirt(RuntimePlugin):

    def __init__(self,name):
        super(RuntimeLibVirt, self).__init__()
        self.uuid=uuid.uuid4()
        self.name=name


    def startRuntime(self):

        import libvirt

        self.conn=libvirt.open("qemu:///system")
        print('KVM Started!\n')