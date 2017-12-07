import sys
import os
import uuid

file_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(file_dir))
VERSION = 1

def run(*args,**kwargs):
    from linux_plugin import Linux
    l = Linux('linux', VERSION, kwargs.get('agent'), str(uuid.uuid4()))
    return l



