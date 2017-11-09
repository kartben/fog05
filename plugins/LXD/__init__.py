import sys
import os


VERSION = 1


def run(*args, **kwargs):
    sys.path.append(os.path.join(sys.path[0], 'plugins', 'LXD'))
    from LXD import LXD
    lxd = LXD('LXD', VERSION, kwargs.get('agent'))
    return lxd

