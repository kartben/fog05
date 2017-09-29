#URI definition

###### updated 29/09/2017

Because we want to share all possibile information through our distributed cache (K,V cache), URI are very important as they are the key for our cache.

## So let's see some examples:

##### Looking for all nodes in a system
`fos://<system_id>/`

##### Looking for basic information about all nodes in the system
`fos://<system_id>/**`

##### Add a plugin to a node
`fos://<system_id>/<node_id>/plugins$add` 

Then the value should be a JSON object with all information that permitt to get and install the plugin

		@AC: I think the URI for adding a plugin should be as follows:
		
			pput(`fos://<system_id>/<node_id>/plugins/<plugin-name>`, plug-in-descr)
			
		As adding this URI to the cache has the effect of "registering" the plugin.
		
			
###### Interact with a runtime
`fos://<system_id>/<node_id>/runtime/<runtime_id>/$action_to_runtime` 

	@GB: see comments below, all actions become desidered state and are passed through the JSON parameter

###### Create a new entity
`fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/$create_entity` 

And the value should be a JSON with all information about this entity

		@AC: Same comment here, the result of a put is equivalente to create
		a new entity. Likewise the remove operation should dispose the entity.
		

##### Interact with an entity
`fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/<entity_id>$action_to_entity`

In this case `action` can be very different things, depend on entity type (vm, unikernel, native app, µSvc...) and can need some value in form of a JSON object

	@AC: If embed actions in the URI I don't think that these should be part of the 
	key used to inster the value in the cache. In other terms, for the URI below:
	
		`fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/<entity_id>$action_to_entity`
		
		The key used by the cache should be only:
		
		`fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/<entity_id>`

	The value associated with a specific key K should represent the desired state for 
	the a specific resource.
	
	
	@GB: As discussed can we use 
	
	`fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/<entity_id>` as key
	
	and the previously defined 'action' become part of the JSON send in the put() or pput()
	
	in a way that we don't have actions inside the uri, but they rappresent a desidered state for that resource
	
	so as example:
	
	previously uri: pput('fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/<entity_id>$run')
	now uri: pput('fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/<entity_id>',{'status':run ... })
	
	
	
## Definition

So after this example we can try to define a more general URI scheme for FogOS

`
fos://<system_id>/<node_id>/<type_of_resource>/<id_of_resource>/<type_of_subresource>/<id_of_subresource>
`

> It is possible to get basic information about all nodes/entity/... at every level by using `**`, where id is required is possible to use wildcard `*` or list of ids
>
> ~~At each level is possible to have `['$'action]['?'query]['#'fragment]`~~ 
>
> At each level is possible to have `['?'query]['#'fragment]`
>
>`<type_of_resource>` can be: 
>
> * plugin
> * runtime
> * network
> * os
>
> `<type_of_subresource>` depend on resource type
> 
> eg for network can be 
> 
> * virtual_network
> * virtual_bridge
> * virtual_interface
> 
>	~~action,~~ query and fragment depend on level
> Action are part of the JSON Object, see below some JSON object types
> 
> At node level is possible to monitor information about a node and manage is lifecycle, the same is possible at id_of_resource level and id_of_subresource level
>
> All values must be JSON objects
