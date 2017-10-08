from interfaces.Store import *
import fnmatch
from threading import Thread
import json

class DStore(Store):

    def __init__(self, root, home, store_id, cache_size, observer):
        self.root = root
        self.home = home
        self.store_id = store_id
        self.__cache_size = cache_size
        self.__observer = observer
        self.__local_cache = {}
        self.__observers = {}
        self.__controller = DController(self)


    def pput(self, uri, value):
        self.__observer.onPput(uri, value)

    def conflict_handler(self, action):
        pass



    def dput(self, uri, values = None):


        if values == None:
            ##status=run&entity_data.memory=2GB
            uri = uri.split('#')
            uri_values = uri[-1]
            uri = uri[0]

        data = {}
        for key in self.__local_cache:
            if fnmatch.fnmatch(key, uri):
                data = json.loads(self.__local_cache.get(key))


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
                values = json.loads(values)
                for k in values.keys():
                    v = values.get(k)
                    if type(v) == list:
                        old_v = data.get(k)
                        v = old_v + v

                    data.update({k: v})
        self.__local_cache.update({uri: json.dumps(data)})
        self.__observer.onPut(uri, json.dumps(data))

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
        for key in self.__local_cache:
            if fnmatch.fnmatch(key, uri):
                data.append({key: self.__local_cache.get(key)})
        if len(data) == 0:
            self.__observer.onMiss()
            print("this is a miss")
        return data

    def put(self, uri, value):
        self.__observer.onPut(uri, value)
        self.__local_cache.update({uri: value})

        for key in self.__observers:
            if fnmatch.fnmatch(uri, key):
                Thread(target=self.__observers.get(key), args=(uri, value)).start()





    def miss_handler(self, action):
        pass

    def iterate(self):
        pass

    def __str__(self):
        ret = ""
        for key, value in self.__local_cache.items():
            ret = str('%s%s' % (ret,str("Key: %s - Value: %s\n" % (key, value))))

        return ret


class DDSObserver(Observer):

    def onRemove(self, uri):
        print('Observer onRemove Called')

    def onConflict(self):
        print('Observer onConflict Called')

    def onDput(self, uri):
        print('Observer onDput Called')

    def onPput(self, uri, value):
        print('Observer onPput Called')

    def onMiss(self):
        print('Observer onMiss Called')

    def onGet(self, uri):
        print('Observer onGet Called')

    def onObserve(self, uri, action):
        print('Observer onObserve Called')

    def onPut(self, uri, value):
        print('Observer onPut Called')


class DDSController(Controller):

    def __init__(self, cache):
        super(DDSController, self).__init__(cache)

    def start(self):
        print('Controller start Called')

    def stop(self):
        print('Controller stop Called')

    def resume(self):
        print('Controller resume Called')

    def pause(self):
        print('Controller pause Called')

