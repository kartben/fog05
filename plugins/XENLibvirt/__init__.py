import sys
import os
file_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(file_dir))

VERSION = 1


def run(*args, **kwargs):
    sys.path.append(os.path.join(sys.path[0], 'plugins', 'XENLibvirt'))
    from XENLibvirt_plugin import XENibvirt
    xen = XENLibvirt('XENLibvirt', VERSION, kwargs.get('agent'), kwargs.get('uuid'),kwargs.get('hypervisor'))
    return xen

