import sys
import os
import uuid

file_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(file_dir))
VERSION = 1

def run(*args,**kwargs):
    from windows_plugin import Windows
    l = Windows('windows', VERSION, kwargs.get('agent'), str(uuid.uuid4()))
    return l



