import sys, os
sys.path.append(os.path.join(sys.path[0].rstrip("tests")))

import uuid
from fog05.DStore import *
from fog05.DController import *
import json
import time

class TestCache():

    def __init__(self):
        self.uuid = '1'


        # Desidered Store. containing the desidered state
        self.droot = "dfos://<sys-id>"
        self.dhome = str("dfos://<sys-id>/%s" % self.uuid)
        self.dstore = DStore(self.uuid, self.droot, self.dhome, 1024)

        # Actual Store, containing the Actual State
        self.aroot = "afos://<sys-id>"
        self.ahome = str("afos://<sys-id>/%s" % self.uuid)
        self.astore = DStore(self.uuid, self.aroot, self.ahome, 1024)

        self.nodes = {}

        self.populateNodeInformation()

    def populateNodeInformation(self):
        node_info = {}

        node_info.update({'name': 'develop node'})
        uri = str('%s/' % self.ahome)
        self.astore.put(uri, json.dumps(node_info))


    def main(self):

        print("Putting on dstore")
        val = {'value': "some value"}
        uri = str('%s/test1' % self.dhome)
        self.dstore.put(uri, json.dumps(val))

        val = {'value2': "some value2"}
        uri = str('%s/test2' % self.dhome)
        self.dstore.put(uri, json.dumps(val))

        val = {'value3': "some value3"}
        uri = str('%s/test3' % self.dhome)
        self.dstore.put(uri, json.dumps(val))

        print("Putting on astore")

        val = {'actual value': "some value"}
        uri = str('%s/test1' % self.ahome)
        self.astore.put(uri, json.dumps(val))

        val = {'actual value2': "some value2"}
        uri = str('%s/test2' % self.ahome)
        self.astore.put(uri, json.dumps(val))

        val = {'actual value32': "some value3"}
        uri = str('%s/test3' % self.ahome)
        self.astore.put(uri, json.dumps(val))

        uri = str('%s/test3' % self.ahome)
        self.astore.put(uri, json.dumps(val))


        print("My UUID is %s" % self.uuid)

        print("###################################### Desidered Store ######################################")
        print(self.dstore)
        print("#############################################################################################")

        print("###################################### Actual Store #########################################")
        print(self.astore)
        print("#############################################################################################")



        input()






if __name__=='__main__':
    agent = TestCache()
    agent.main()

