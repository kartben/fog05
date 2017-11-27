# Fog05


Unifies compute/networking fabric end-to-end

Thanks to its plugin architecture can manage near everything

See inside [docs](../docs) for some design documentation

Inside [src/plugins](../plugins) there are some plugins for entity

Inside [src/examples](../examples) you can find some example/demo



## Agent

You should have OpenSplice installed, and [Python ATO DDS API Bindings](https://github.com/atolab/dds-python)



---

config dependencies:

- user should be able to use sudo without password asking (`echo "username  ALL=(ALL) NOPASSWD: ALL"  >> /etc/sudoers`)

## Installation

Run `python3 setup.py install`


### How to run:


There are two ways to run a fog05 node

1st:

Open a python3 interpreter
    
    $ python3
    >>> from fog05.fosagent import FosAgent
    >>> a = FosAgent()
    >>> a.run()
    ....
    >>> a.stop()

You can pass to the constructor the plugins directory `FosAgent(plugins_path="/path/to/plugins")`
or debug=False to have logging on file

2nd:

Using the fos command
    
    $ fos start <path_to_plugins>