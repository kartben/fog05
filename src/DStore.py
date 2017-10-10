from interfaces.Store import *
from DController import *
import fnmatch
from threading import Thread
import json

class DStore(Store):

    def __init__(self, store_id, root, home, cache_size):
        super(DStore, self).__init__()
        self.root = root
        self.home = home
        self.store_id = store_id
        self.__store = {} # This stores URI whose prefix is **home**
        self.__cache_size = cache_size
        self.__local_cache = {} # this is a cache that stores up
                                # to __cache_size entry for URI whose prefix is not **home**
        self.__observers = {}
        self.__controller = DController(self)
        self.__controller.start()


    def is_stored_value(self, uri):
        return fnmatch.fnmatch(uri, self.home)

    def is_cached_value(self, uri):
        return  not self.is_stored_value(uri)


    def get_version(self, uri):
        version = None
        v = None
        if self.is_stored_value(uri):
            if uri in self.__store:
                v = self.__store[uri]
        else:
            if uri in self.__local_cache:
                v = self.__local_cache[uri]

        if v != None:
            version = v[1]

        return version

    def get_value(self, uri):
        v = None
        if self.is_stored_value(uri):
            if uri in self.__store:
                v = self.__store[uri]
        else:
            if uri in self.__local_cache:
                v = self.__local_cache[uri]


        return v

    def next_version(self, uri):
        nv = 0
        v = self.get_version(uri)
        if v != None:
            nv = v +1

        return nv

    def __unchecked_store_value(self, uri, value, version):
        if self.is_stored_value(uri):
            self.__store[uri] = (value, version)
        else:
            self.__local_cache[uri] = (value, version)


    def update_value(self, uri, value, version):
        succeeded = False

        current_version = self.get_version(uri)
        if current_version != None:
            if current_version < version:
                self.__unchecked_store_value(uri, value, version)
                succeeded = True
        else:
            self.__unchecked_store_value(uri, value, version)
            succeeded = True


        return succeeded

    def notify_observers(self, uri, value, v):
        # AC: Should not use a separate thread of each observer... This is going to result in a
        #     few DDS writes which are non-blocking and thus not so useful to start a separate thread
        for key in self.__observers:
            if fnmatch.fnmatch(uri, key):
                Thread(target=self.__observers.get(key), args=(uri, value, v)).start()

    def put(self, uri, value):
        v = self.get_version(uri)
        if v == None:
            v = 0
        else:
            v = v + 1
        self.update_value(uri, value, v)

        # It is always the observer that inserts data in the cache
        self.__controller.onPut(uri, value, v)
        self.notify_observers(uri, value, v)


    def pput(self, uri, value):
        v = self.next_version(uri)
        self.__unchecked_store_value(uri, value, v)
        self.__controller.onPput(uri, value, v)
        self.notify_observers(uri, value, v)


    def conflict_handler(self, action):
        pass



    def dput(self, uri, values = None):
        version = self.next_version(uri)
        if values == None:
            ##status=run&entity_data.memory=2GB
            uri = uri.split('#')
            uri_values = uri[-1]
            uri = uri[0]

        data = {}
        for key in self.__local_cache:
            if fnmatch.fnmatch(key, uri):
                data = json.loads(self.__local_cache.get(key)[0])


        # @TODO: Need to resolve this miss
        if len(data) == 0:
            print("this is a miss")
            return
        else:

            if values == None:
                uri_values = uri_values.split('&')
                for tokens in uri_values:
                    v = tokens.split('=')[-1]
                    k = tokens.split('=')[0]
                    if len(k.split('.')) < 2:
                        data.update({k: v})
                    else:
                        d = self.dot2dict(k, v)
                        # @TODO: update in a best way
                        data.update(d) #not very safe
            else:
                values = json.loads(values)
                for k in values.keys():
                    v = values.get(k)
                    if type(v) == list:
                        old_v = data.get(k)
                        v = old_v + v

                    data.update({k: v})

        value = json.dumps(data)
        self.__unchecked_store_value(uri, value , version)
        self.__controller.onDput(uri, value, version)
        self.notify_observers(uri, value, version)





    def observe(self, uri, action):
        self.__observers.update({uri: action})

    def remove(self, uri):
        self.__controller.onRemove(uri)
        self.__local_cache.pop(uri)

    def get(self, uri):
        v = self.get_value(uri)
        if v == None:
            print("this is a miss")
            self.__controller.onMiss()
            rv = self.__controller.resolve(uri)
            if rv != None:
                self.update_value(uri, v[0], v[1])
                self.notify_observers(uri, v[0], v[1])
                v = rv

        return v[0]



    def miss_handler(self, action):
        pass

    def iterate(self):
        pass

    def __str__(self):
        ret = ""
        for key, value in self.__local_cache.items():
            ret = str('%s%s' % (ret,str("Key: %s - Value: %s\n" % (key, value))))

        return ret

    #convert dot notation to a dict
    def dot2dict(self, dot_notation, value=None):
        ld = []

        tokens = dot_notation.split('.')
        n_tokens = len(tokens)
        # print(tokens)
        # print(n_tokens)
        for i in range(n_tokens, 0, -1):
            # print(i)
            # print(tokens[i-1])
            if i == n_tokens and value is not None:
                ld.append({tokens[i - 1]: value})
            else:
                ld.append({tokens[i - 1]: None})

            '''
            if i == 0:
                d.update({tokens[i]:{}})
            if i < n_tokens and i >0:
                d.get(tokens[i-1]).update({tokens[i]: {}})
            if i == n_tokens:
                d.update({tokens[i]:None})
            '''
        # print (ld)
        for i in range(0, len(ld) - 1):
            k = list(ld[i + 1].keys())
            # print (k[0])
            # print (ld[i])
            ld[i + 1].update({k[0]: ld[i]})
            # print (ld)
        # print (ld)
        return ld[len(ld) - 1]

#
# class DDSObserver(Observer):
#
#     def onRemove(self, uri):
#         print('Observer onRemove Called')
#
#     def onConflict(self):
#         print('Observer onConflict Called')
#
#     def onDput(self, uri):
#         print('Observer onDput Called')
#
#     def onPput(self, uri, value):
#         print('Observer onPput Called')
#
#     def onMiss(self):
#         print('Observer onMiss Called')
#
#     def onGet(self, uri):
#         print('Observer onGet Called')
#
#     def onObserve(self, uri, action):
#         print('Observer onObserve Called')
#
#     def onPut(self, uri, value):
#         print('Observer onPut Called')
#
#
# class DDSController(Controller):
#
#     def __init__(self, cache):
#         super(DDSController, self).__init__(cache)
#
#     def start(self):
#         print('Controller start Called')
#
#     def stop(self):
#         print('Controller stop Called')
#
#     def resume(self):
#         print('Controller resume Called')
#
#     def pause(self):
#         print('Controller pause Called')
#
