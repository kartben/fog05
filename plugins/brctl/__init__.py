import sys
import os


VERSION = 1

def run(*args,**kwargs):

    sys.path.append(os.path.join(sys.path[0], 'plugins', 'brctl'))
    from brctl import brctl
    br = brctl('brctl', VERSION, kwargs.get('agent'))
    return br

