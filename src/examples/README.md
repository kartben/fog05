## Fog05 Examples

In this directory you can find some example of what Fog05 can do.

 - [Lifecycle of a VM](https://github.com/atolab/FogOS/blob/master/src/examples/lf_vm.py)
 - [Lifecycle of a native application](https://github.com/atolab/FogOS/blob/master/src/examples/lf_native.py)
 - [Lifecycle of a ROS2 Nodelet](https://github.com/atolab/FogOS/blob/master/src/examples/lf_ros2.py)
 - [Complex application onboarding](https://github.com/atolab/FogOS/blob/master/src/examples/app_onboard.py)
 - [VM Migration](https://github.com/atolab/FogOS/blob/master/src/examples/vm_migration.py)
 
 #### How to run examples:
 
 You need to start everything from `src` directory
 
    cd FogOS/src/
    python3 examples/<example_file>.py
    
The in another terminal simply start the Agent
    
    cd FogOS/src/
    python3 fogagent.py