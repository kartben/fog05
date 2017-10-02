class NodeCache(object):

    def __init__(self,local_informatio_cache_size,remote_information_cache_size,node_id,hashing_function):
        raise NotImplementedError

    def put(self,uri,value):
        """
        uri eg. xrce://{nodeid or */** (* is only node ids, ** is all informations) or list of nodeids}/resurce
        value json obj
        """
        raise NotImplementedError

    def pput(self,uri,value):
        """
        Persistent put, in other terms this (k,v) will be restored when re-creating a cache with the same scope.

        uri eg. xrce://{nodeid or */** (* is only node ids, ** is all informations) or list of nodeids}/resurce
        value json obj
        """
        raise NotImplementedError

    def dput(self, uri):
        """
        :param uri: the URI for which a delta-put has to be applied. A delta put updates only the
                    attributes inlined in the URI, e.g.
                    dput('fos://<system_id>/<node_id>/runtime/<runtime_id>/entity/<entity_id>#status=run&entity_data.memory=2GB')
                    The other attributes, if any, associated with the
                    current value of he URI are left unchanged.

        """
        raise NotImplementedError

    def dput(self, uri, value):
        """
        :param uri: the URI for which a delta-put has to be applied. A delta put updates only the
                    attributes provided by the value. The other attributes, if any, associated with the
                    current value of he URI are left unchanged.
        """
    def get(self,uri):
        """
        :return: dict (uri,value)
        """
        raise NotImplementedError

    def remove(self, uri):
        """
            removes the entry associated to this URI from the distributed cache.
        """
        raise NotImplementedError


    def observe(self,uri, action):
        """
        action(cache) is a lambda
        """
        raise NotImplementedError

    def iterate(self):
        """
        iterate into local cache
        """
        raise NotImplementedError


    def miss_handler(self,action):
        raise NotImplementedError

    def conflict_handler(self,action):
        raise NotImplementedError


