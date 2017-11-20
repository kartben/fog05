import sys
import os


VERSION = 1

def run(*args,**kwargs):
    from .linux import Linux
    l = Linux('linux', VERSION, kwargs.get('agent'))
    return l

