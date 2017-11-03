## Fog05 Examples

In this directory you can find some example of what Fog05 can do.

 - [Lifecycle of a VM](lf_vm.py)
 - [Lifecycle of a native application](lf_native.py)
 - [Lifecycle of a ROS2 Nodelet](lf_ros2.py)
 - [Complex application onboarding](app_onboard.py)
 - [VM Migration](vm_migration.py)
 
 #### How to run examples:
 
 You need to start example from `src` directory
 
    cd FogOS/src/
    python3 examples/<example_file>.py
    
Then in another terminal simply start the Agent
    
    cd FogOS/src/
    python3 fogagent.py
    
The VM migration example need two different nodes, and they should be configured to allow ssh access with publickey 
and maybe the same username (this is for libvirt connection, otherwise migration will fail)