import sys
import os


VERSION = 1

def run(*args,**kwargs):

    sys.path.append(os.path.join(sys.path[0],'plugins','RuntimeLibVirt'))
    from RuntimeLibVirt import RuntimeLibVirt
    kvm = RuntimeLibVirt('kvm-libvirt',VERSION)
    return kvm

