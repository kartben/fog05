#URI definition

Because we want to share all possibile information through our distributed cache (K,V cache), URI are very important as they are the key for our cache.

## So let's see some examples:

##### Looking for all nodes in a system
`fos://<system_id>/`

##### Looking for basic information about all nodes in the system
`fos://<system_id>/**`

##### Add a plugin to a node
`fos://<system_id>/<node_id>/plugins$add` 

Then the value should be a JSON object with all information that permitt to get and install the plugin

###### Interact with a runtime
`fos://<system_id>/<node_id>/runtime/<runtime_id>/$action_to_runtime` 

###### Create a new entity
`fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/$create_entity` 

And the value should be a JSON with all information about this entity

##### Interact with an entity
`fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/<entity_id>$action_to_entity`

In this case `action` can be very different things, depend on entity type (vm, unikernel, native app, µSvc...) and can need some value in form of a JSON object


## Definition

So after this example we can try to define a more general URI scheme for FogOS

`
fos://<system_id>/<node_id>/<type_of_resource>/<id_of_resource>/<type_of_subresource>/<id_of_subresource>
`

> It is possible to get basic information about all nodes/entity/... at every level by using `**`, where id is required is possible to use wildcard `*` or list of ids

> At each level is possible to have `['$'action]['?'query]['#'fragment]` 

>`<type_of_resource>` can be: 

> * plugin
> * runtime
> * network
> * os

> `<type_of_subresource>` depend on resource type
> 
> eg for network can be 
> 
> * virtual_network
> * virtual_bridge
> * virtual_interface
> 
>  action, query and fragment depend on level
> 
> 
> At node level is possible to monitor information about a node and manage is lifecycle, the same is possible at id_of_resource level and id_of_subresource level

> All values must be JSON objects