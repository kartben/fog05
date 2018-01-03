# fog05


Unifies compute/networking fabric end-to-end

Thanks to its plugin architecture can manage near everything

See inside [docs](https://github.com/atolab/fog05_docs/tree/master/docs) for some design documentation

Inside [plugins](./plugins) there are some plugins for entity

Inside [examples](./examples) you can find some example/demo



## Agent

You should have [OpenSplice](https://github.com/ADLINK-IST/opensplice) installed, and [Python ATO DDS API Bindings](https://github.com/atolab/dds-python)



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
    
    $ fos start -p <path_to_plugins> [-v to get verbose output, -d to run as a daemon]
    

### Interact with the nodes


To interact with the nodes deployed you can use the fos cli interface

    $ fos -h [ to get the help]
    usage: fos [-h] {start,node,network,entity,manifest} ...

     Fog05 | The Fog-Computing IaaS

    positional arguments:
    {start,node,network,entity,manifest}

    optional arguments:
    -h, --help            show this help message and exit
    
List all nodes:

    $ fos node list
    
List all entities:

    $ fos entitity list
    
List all networks:

    $ fos network list
    
Adding a plugin to a node:


    $ fos node -u <node uuid> -a -p -m <path to plugin manifest>

Information about a node:

    $ fos node -u <node uuid> [-i detailed information | -p information about plugins]

Add a network to a node

    $ fos network -u <node uuid> -a -m <network manifest>


Simple lifecycle of an entity:

    $ fos entity -u <node_uuid> --define -m <entity manifest>
    $ fos entity -u <node uuid> -eu <entity uuid> --configure
    $ fos entity -u <node uuid> -eu <entity uuid> --run
    $ fos entity -u <node uuid> -eu <entity uuid> --stop
    $ fos entity -u <node uuid> -eu <entity uuid> --clean
    $ fos entity -u <node uuid> -eu <entity uuid> --undefine
    
Migration of an entity

    fos entity -u <current node uuid> -eu <entity uuid> -du <destination node uuid> --migrate