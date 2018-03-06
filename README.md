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

Installation script tested on ubuntu 16.04

    sudo ./install.sh

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


Simple lifecycle of an atomic entity:

    $ fos entity -u <node_uuid> --define -m <atomic entity manifest>
    $ fos entity -u <node uuid> -eu <atomic entity uuid> --configure -iu <instance_uuid>
    $ fos entity -u <node uuid> -eu <atomic entity uuid> --run -iu <instance_uuid>
    $ fos entity -u <node uuid> -eu <atomic entity uuid> --stop -iu <instance_uuid>
    $ fos entity -u <node uuid> -eu <atomic entity uuid> --clean -iu <instance_uuid>
    $ fos entity -u <node uuid> -eu <atomic entity uuid> --undefine
    
Migration of an atomic entity

    fos entity -u <current node uuid> -eu <entity uuid> -du <destination node uuid>  -iu <instance_uuid> --migrate
    
Static Onboard entity (DAG of Atomic Entities)

    $ fos entity --add -m <entity manifest>

Only static and simple resource managment is available at the moment, you can find an example of a DAG Entity in this [example](./examples/manifest/example_entity.json)

### CLI utils

With fos-get you can explore the distributed store

    fos-get -u <URI>

There is also available a logger to see the evolution of the distributed store and all information coming from nodes.

    f05log <store root>
    
### fog05 WebSocket Store server

The store server providing websocket api can be started by:

    $ f05ws    
    
    
### fog05 Web Client

The web client can be operated interactively by starting it as:

    $ f05wc

Otherwise you can submit commamnds using a file as in:

    $ cat ./examples/scripts/cmd.fosw | f05wc
    $ printf get 1 fos://root/home/cn0 | python3 f05wc
