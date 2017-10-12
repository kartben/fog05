# Service Definition

To deploy a complex application/service the first thing to do is to define a manifest file,
those file should contain all information needed to correctly deploy the application/service,
so it should describe all entities and dependencies between these entities that compose the application/service.

---

### Application/Service manifest file

This file describe how to deploy the application/service, so it should contain:

- description of application/service
- entities that compose the application/service (eg. database server, http server...)
- relations and constraints between entities
- path to manifest files of components


So this describe the "graph" of the application/service
Then with this file the agent can decide where deploy the application/service

---

### Component manifest file

This file describe the single component of an application/service so it should describe
some low level information needed to deploy the component, so it should contain:

- description of component
- entity type (vm, unikernel, , µSvc, Ros Nodelet, native app...)
- entity description (depend on entity type)
- eventual need of hw acceleration or specific I/O

---

Should be agent's work to start the components in the correct order and with correct relations


---

##### Examples

Example of a simple 'complex' application: a Wordpress blog

    @GB: In the case of a service should have some information on how to scale
     in the 'need' key we now have a dictionary in which the key is the name of the needed
     component and the value is an int that rappresent the Proximity Class (lower is closer)
     

![graph](../img/example_service.png)


Application manifest:

    {
        "name":"wp_blog"
        "description":"simple wordpress blog",
        "components":[
            {
                "name":"wordpress",
                "need":[{"mysql":3}],
                "manifest":"/some/path/to/wordpress_manifest.json"
            },
            {
                "name":"mysql",
                "need":[],
                "manifest":"/some/path/to/mysql_manifest.json"
            }
        ]
    }


Wordpress manifest:

    {
        "name":"wp_v2.foo.bar"
        "description":"wordpress blog engine"
        "type":"container",
        "entity_description":{...},
        "accelerators":[]
        "io":[]
    }

mysql manifest file:

    {
        "name":"myql_v2.foo.bar"
        "description":"mysql db engine"
        "type":"vm",
        "entity_description":{...},  <- here all information to download and configure the db server
        "accelerators":[]
        "io":[]
    }
 