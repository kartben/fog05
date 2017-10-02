from interfaces.Cache import *
import fnmatch


class DDSCache(Cache):

    def __init__(self, local_information_cache_size, node_id, observer):
        self.__local_size = local_information_cache_size
        self.__node_id = node_id
        self.__observer = observer
        self.__local_cache = {}
        self.__observers = {}


    def pput(self, uri, value):
        pass

    def conflict_handler(self, action):
        pass

    def dput(self, uri):
        pass

    def observe(self, uri, action):
        self.__observers.update({uri: action})

    def remove(self, uri):
        self.__observer.onRemove(uri)
        self.__local_cache.pop(uri)

    def get(self, uri):
        data = []
        uri = str("%s%s" % (uri, '*'))
        self.__observer.onGet(uri)
        for key in self.__local_cache:
            if fnmatch.fnmatch(key, uri):
                data.append({key: self.__local_cache.get(key)})
        if len(data) == 0:
            self.observer.onMiss()
            print("this is a miss")
        return data

    def put(self, uri, value):
        self.__observer.onPut(uri, value)
        self.__local_cache.update({uri: value})

        for key in self.__observers:
            if fnmatch.fnmatch(uri, key):
                self.__observers.get(key)(uri, value)





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

