from interfaces.Store import *
import fnmatch
from threading import Thread
import json
import redis





class RedisObserver(Observer):

    def __init__(self):
        self.redis = redis.StrictRedis(host='localhost', port=6379)  # Connect to local Redis instance
        self.p = self.redis.pubsub()
        self.update_thread = Thread(target=self.updates)
        self.update_thread.start()

    def updates(self):
        for m in self.p.listen():
            self.p.get_messages()

    def onRemove(self, uri):
        self.redis.delete(uri)

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
        return self.redis.get(uri)

    def onObserve(self, uri, action):
        self.p.psubscribe(**{uri: action})
        print('Observer onObserve Called')

    def onPut(self, uri, value):
        print('Observer onPut Called')
        self.redis.set(uri, value)


class RedisController(Controller):

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

