import sys
import os

file_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(file_dir))

VERSION = 1

def run(*args,**kwargs):

    sys.path.append(os.path.join(sys.path[0], 'plugins', 'ros2'))
    from ros2_file import ROS2
    n = ROS2('ros2', VERSION, kwargs.get('agent'))
    return n

