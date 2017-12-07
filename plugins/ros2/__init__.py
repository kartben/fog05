import sys
import os

file_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(file_dir))

VERSION = 1

def run(*args,**kwargs):

    from ros2_file import ROS2
    n = ROS2('ros2', VERSION, kwargs.get('agent'), kwargs.get('uuid'))
    return n

