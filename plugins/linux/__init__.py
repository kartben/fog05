import sys
import os

file_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(file_dir))
VERSION = 1

def run(*args,**kwargs):
    from linux_plugin import Linux
    l = Linux('linux', VERSION, kwargs.get('agent'))
    return l



