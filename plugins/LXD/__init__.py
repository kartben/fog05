import sys
import os
file_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(file_dir))

VERSION = 1


def run(*args, **kwargs):
    sys.path.append(os.path.join(sys.path[0], 'plugins', 'LXD'))
    from LXD_plugin import LXD
    lxd = LXD('LXD', VERSION, kwargs.get('agent'), kwargs.get('uuid'))
    return lxd

