import uuid
import sys
import os
sys.path.append(os.path.join(sys.path[0].rstrip("tests")))
from DStore import *
import dds
import json
import time


class Controll():
    def __init__(self):
        self.uuid = uuid.uuid4()
        sid = str(self.uuid)
        self.root = "fos://<sys-id>"
        self.home = str("fos://<sys-id>/%s" % sid)
        self.nodes = {}
        # Notice that a node may have multiple caches, but here we are
        # giving the same id to the nodew and the cache
        self.store = DStore(sid, self.root, self.home, 1024)

    def nodeDiscovered(self, uri, value, v=None):
        value = json.loads(value)
        print(value)
        if uri != str('fos://<sys-id>/%s/' % self.uuid):
            print("###########################")
            print("###########################")
            print("### New Node discovered ###")
            print("UUID: %s" % value.get('uuid'))
            print("Name: %s" % value.get('name'))
            print("###########################")
            print("###########################")
            self.nodes.update({len(self.nodes) + 1: {value.get('uuid'): value}})
            self.show_nodes()

    def test_observer(self, key, value, v):
        print ("###########################")
        print ("##### I'M an Observer #####")
        print ("## Key: %s" % key)
        print ("## Value: %s" % value)
        print ("## V: %s" % v)
        print ("###########################")
        print ("###########################")

    def show_nodes(self):
        for k in self.nodes.keys():
            n = self.nodes.get(k)
            id = list(n.keys())[0]
            print("%d - %s : %s" % (k, n.get(id).get('name'), id))


    def lot_of_puts(self,node_uuid):

        for i in range(0, 2):
            val = {'test': str("put no: %d" % i)}
            uri = str('fos://<sys-id>/%s/info' % node_uuid)
            # time.sleep(1)
            self.store.put(uri, json.dumps(val))

    def main(self, master=True):

        uri = str('fos://<sys-id>/*')
        self.store.observe(uri, self.nodeDiscovered)
        key42 = 'fos://<sys-id>/42'
        key21 = 'fos://<sys-id>/21'

        if master:
            print("Running as Master")
            while len(self.nodes) == 0:
                print("Looking for stores...")
                self.show_nodes()
                time.sleep(2)


            node_uuid = self.nodes.get(1)
            if node_uuid is not None:
                node_uuid = list(node_uuid.keys())[0]
                if node_uuid is not None:
                    pass
            else:
                exit()

            input("Press enter to send")

            print(" >>>> This should not cause a miss! <<<<< ")
            v = self.store.get(key42)
            print("Reolved: {0}".format(v))
            print(" >>>> This shoud miss! <<<<< ")
            v = self.store.get(key21)
            print("Reolved: {0}".format(v))


            self.lot_of_puts(node_uuid)



        else:
            print("Running as delegate")
            val = {'uuid': str(self.uuid), "name": "slave"}
            uri = str('fos://<sys-id>/%s/' % self.uuid)

            val42 = {
                'key': key42,
                'value': 'the ultimate truth'
            }
            self.store.put(key42, json.dumps(val42))


            self.store.put(uri, json.dumps(val))


            uri = str('fos://<sys-id>/%s/info' % self.uuid)
            self.store.observe(uri, self.test_observer)

            while True:
                print("Delegate done with writing...")
                time.sleep(10)

        input()

        exit(0)


if __name__ == '__main__':
    rt = dds.Runtime()
    c = Controll()
    print (len(sys.argv))
    if len(sys.argv) == 1:
        c.main()
    else:
        c.main(False)
