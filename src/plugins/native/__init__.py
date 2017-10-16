import sys
import os


VERSION = 1

def run(*args,**kwargs):

    sys.path.append(os.path.join(sys.path[0], 'plugins', 'native'))
    from native import Native
    n = Native('native', VERSION, kwargs.get('agent'))
    return n

