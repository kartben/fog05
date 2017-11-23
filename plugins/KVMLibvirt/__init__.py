import sys
import os
file_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(file_dir))

VERSION = 1


def run(*args, **kwargs):
    sys.path.append(os.path.join(sys.path[0], 'plugins', 'KVMLibvirt'))
    from KVMLibvirt_plugin import KVMLibvirt
    kvm = KVMLibvirt('KVMLibvirt', VERSION, kwargs.get('agent'))
    return kvm

