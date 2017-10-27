import sys
import os


VERSION = 1

def run(*args,**kwargs):

    sys.path.append(os.path.join(sys.path[0], 'plugins', 'ros2'))
    from ros2 import ROS2
    n = ROS2('ros2', VERSION, kwargs.get('agent'))
    return n

