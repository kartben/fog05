import sys
import os


VERSION = 1

def run(*args,**kwargs):

    sys.path.append(os.path.join(sys.path[0], 'plugins', 'random_mano'))
    from random_mano import RandomMANO
    n = RandomMANO('random_mano', VERSION, kwargs.get('agent'))
    return n

