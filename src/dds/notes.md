## Distributed Cache: Main Idea

The distributed cache we are designing stores <key,value> tuples where
the key i a URI. Each cache has a root URI that identifies the point
in the URI hierarchy in which the cache is attached. Anything below
this point is maintained in always memory. Everything else is
maintained in a fiexed size cache were replacements take place because
of capacity and conflicts.

In the case of FogOS the URI are identified by the scheme "fos://",
thus a generic cache is associated with a home **H** of the type:

       fos://system-id/node-id/a/b/c

Notice that a cache home is not supposed to have wildcards.

A cache has also associated a root **R** that is used to identify the
scope at whch miss are resolved. As an example, the base for the cache with home **H** could be:

      	 fos://system-id

This would constrain the resolution of misses within a system. 

The cache allows to store data as volatile or
persistent. Additionally, it is possible to specify that a put
represents a delta update.

## DDS Mapping 

Given a cache **Ci** with home **Hi** and a root **R**, the current
implementation defines the following partitions:

- **Hi** is used to write the local data. A writer with persistent QoS
  writes persistent tuples in this partition too.

- **R** is used to resolve miss, distribute updates,  
    invalidate cache entries.

- Observers are implemented by attaching a reader to the roots **Ri**
  of the caches that match the observe expression.



## Meeting Notes

- We need to add a delta-remote

- A cache abstraction is used uniformly and a cache can be backed-up
  by a store

- We could distinguish between the cache storing desired state and the
  cache storing the actual state. Only the owner of the data has the
  rights to update the actual state.
  


