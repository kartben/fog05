import sys
import os


VERSION = 1


def run(*args, **kwargs):
    sys.path.append(os.path.join(sys.path[0], 'plugins', 'KVMLibvirt'))
    from KVMLibvirt import KVMLibvirt
    kvm = KVMLibvirt('KVMLibvirt', VERSION, kwargs.get('agent'))
    return kvm

