import sys
import os


VERSION = 1

def run(*args,**kwargs):

    sys.path.append(os.path.join(sys.path[0],'plugins','linux'))
    from linux import Linux
    l = Linux('linux',VERSION)
    return l

