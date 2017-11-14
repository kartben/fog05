import sys, os
sys.path.append(os.path.join(sys.path[0].rstrip("tests")))

import uuid
from fog05.DStore import *
from fog05.DController import *
import json
import time

class TestCache():

    def __init__(self):
        self.duuid = 'd2'
        self.auuid = 'a2'
        self.uuid = '2'
        sid = str(self.uuid)


        # Desidered Store. containing the desidered state
        self.droot = "dfos://<sys-id>"
        self.dhome = str("dfos://<sys-id>/%s" % sid)
        # AC: Notice that store IDs have to be unique, if that is not the case
        #     a store may mistaken a remote request for its own.
        self.dstore = DStore(self.duuid , self.droot, self.dhome, 1024)

        # Actual Store, containing the Actual State
        self.aroot = "afos://<sys-id>"
        self.ahome = str("afos://<sys-id>/%s" % sid)
        self.astore = DStore(self.auuid , self.aroot, self.ahome, 1024)

        self.nodes = {}


    def main(self):


        input("Press enter to try miss handling")

        v = self.dstore.get("dfos://<sys-id>/1/test1")
        print(v)

        input("Next...")

        v = self.dstore.get("dfos://<sys-id>/1/test2")
        print(v)

        input("Next...")

        v = self.dstore.get("dfos://<sys-id>/1/test3")
        print(v)

        input("Next...")


        v = self.astore.get("afos://<sys-id>/1/")
        print(v)

        input("Next...")


        v = self.astore.get("afos://<sys-id>/1/test1")
        print(v)

        input("Next...")

        # a resolve operates over a trivial URI not over a wildcard
        # v = self.astore.get("afos://<sys-id>/*/test2")
        # print(v)

        v = self.astore.get("afos://<sys-id>/1/test2")
        print(v)

        input("Next...")


        input()
        exit(0)

        #################


if __name__=='__main__':
    agent = TestCache()
    agent.main()

