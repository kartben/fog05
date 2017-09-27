class NodeCache():

    def __init__(self,local_informatio_cache_size,remote_information_cache_size,node_id,hashing_function):
        raise NotImplementedError

    def put(self,uri,value):
        """
        uri eg. xrce://{nodeid or */** (* is only node ids, ** is all informations) or list of nodeids}/resurce
        value json obj
        """
        raise NotImplementedError

    def get(self,uri):
        """
        :return: dict (uri,value)
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


