import uuid
import sys
import os

from fog05.DStore import *
import json
import time


class Controll():
    def __init__(self):
        self.uuid = uuid.uuid4()
        sid = str(self.uuid)

        '''
        Creating the two stores
        
        afos://...  Actual State Store
        In this store you can find all the actual data of the node, this store is written by
        plugins and by the fogagent for update the store after a request.
        All other nodes can read or observe only this store.
        
        
        dfos://... Desidered State Store
        In this store other nodes write the command/request, all plugins and the agent observe this store,
        in a way that they can react to a desidered state
        
        '''


        self.droot = "dfos://<sys-id>"
        self.dhome = str("dfos://<sys-id>/%s" % sid)
        self.dstore = DStore(sid, self.droot, self.dhome, 1024)

        self.aroot = "afos://<sys-id>"
        self.ahome = str("afos://<sys-id>/%s" % sid)
        self.astore = DStore(sid, self.aroot, self.ahome, 1024)

        self.nodes = {}




    def nodeDiscovered(self, uri, value, v = None):
        '''

        This is an observer for discover new nodes on the network
        It is called by the DStore object where it was registered.
        If a new node is discovered it will be added to the self.nodes dict

        :param uri:
        :param value:
        :param v:
        :return:
        '''
        value = json.loads(value)
        if uri != str('fos://<sys-id>/%s/' % self.uuid):
            print ("###########################")
            print ("###########################")
            print ("### New Node discovered ###")
            print ("UUID: %s" % value.get('uuid'))
            print ("Name: %s" % value.get('name'))
            print ("###########################")
            print ("###########################")
            self.nodes.update({ len(self.nodes)+1 : {value.get('uuid'): value}})


    def show_nodes(self):
        '''
        Print all nodes discovered by this script

        :return:
        '''
        for k in self.nodes.keys():
            n = self.nodes.get(k)
            id = list(n.keys())[0]
            print("%d - %s : %s" % (k, n.get(id).get('name'), id))




    def main(self):

        # registering an observer for all actual store root in this system
        # this allow the discovery of new nodes
        uri = str('afos://<sys-id>/*/')
        self.astore.observe(uri, self.nodeDiscovered)


        while True:
            uri = str('afos://<sys-id>/*/')
            nodes = json.loads(self.astore.get(uri))
            print(nodes)
            time.sleep(10)


if __name__ == '__main__':
    c = Controll()
    c.main()
