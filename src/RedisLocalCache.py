from interfaces.Cache import *
import fnmatch
from threading import Thread
import json
import redis

class RedisCache(Cache):

    def __init__(self, local_information_cache_size, node_id, observer):
        self.__local_size = local_information_cache_size
        self.__node_id = node_id
        self.__observer = observer
        self.__observers = {}
        self.cache = redis.Redis(host='localhost', port=6379, db=0)
        self.cache.config_set('maxmemory', str('%dmb' % self.__local_size))


    def pput(self, uri, value):
        self.__observer.onPput(uri, value)

    def conflict_handler(self, action):
        pass

    def dput(self, uri):
        self.__observer.onDput(uri)
        ##status=run&entity_data.memory=2GB
        uri = uri.split('#')
        values = uri[-1]
        uri = uri[0]
        data = {}
        keys = self.cache.keys(pattern=uri)
        for k in keys:
            data.append({k: json.loads(self.cache.get(k))})
        if len(data) == 0:
            self.__observer.onMiss()
            print("this is a miss")
        else:
            values = values.split('&')
            for tokens in values:
                v = tokens.split('=')[-1]
                k = tokens.split('=')[0]
                if len(k.split('.')) < 2:
                    data.update({k: v})

        print(data)
        self.cache.set(uri, json.dumps(data))

        for key in self.__observers:
            if fnmatch.fnmatch(uri, key):
                Thread(target=self.__observers.get(key), args=(uri, json.dumps(data))).start()






    def observe(self, uri, action):
        self.__observers.update({uri: action})

    def remove(self, uri):
        self.__observer.onRemove(uri)
        self.__local_cache.pop(uri)

    def get(self, uri):
        data = []
        #uri = str("%s%s" % (uri, '*'))
        self.__observer.onGet(uri)
        keys = self.cache.keys(pattern=uri)
        for k in keys:
            data.append({k: self.cache.get(k)})
        if len(data) == 0:
            self.__observer.onMiss()
            print("this is a miss")
        return data

    def put(self, uri, value):
        self.__observer.onPut(uri, value)
        self.cache.set(uri, value)

        for key in self.__observers:
            if fnmatch.fnmatch(uri, key):
                Thread(target=self.__observers.get(key), args=(uri, value)).start()





    def miss_handler(self, action):
        pass

    def iterate(self):
        pass

    def __str__(self):
        ret = ""
        for key in self.cache.keys():
            ret = str('%s%s' % (ret,str("Key: %s - Value: %s\n" % (key, self.cache.get(key)))))

        return ret
