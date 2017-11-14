import sys, os
sys.path.append(os.path.join(sys.path[0].rstrip("tests")))

import uuid
from fog05.DStore import *
from fog05.DController import *
import json
import time

class TestCache():

    def __init__(self):
        self.uuid = '2'
        sid = str(self.uuid)


        # Desidered Store. containing the desidered state
        self.droot = "dfos://<sys-id>"
        self.dhome = str("dfos://<sys-id>/%s" % sid)
        self.dstore = DStore(sid, self.droot, self.dhome, 1024)

        # Actual Store, containing the Actual State
        self.aroot = "afos://<sys-id>"
        self.ahome = str("afos://<sys-id>/%s" % sid)
        self.astore = DStore(sid, self.aroot, self.ahome, 1024)

        self.nodes = {}


    def main(self):


        input("Press enter to try miss handling")

        v = self.dstore.get("dfos://<sys-id>/1/test1")
        print(v)

        v = self.dstore.get("dfos://<sys-id>/1/test2")
        print(v)

        v = self.dstore.get("dfos://<sys-id>/1/test3")
        print(v)

        v = self.astore.get("afos://<sys-id>/1/")
        print(v)

        v = self.astore.get("afos://<sys-id>/1/test1")
        print(v)

        # a resolve operates over a trivial URI not over a wildcard
        # v = self.astore.get("afos://<sys-id>/*/test2")
        # print(v)

        v = self.astore.get("afos://<sys-id>/1/test2")
        print(v)



        input()
        exit(0)

        #################


if __name__=='__main__':
    agent = TestCache()
    agent.main()

