import asyncio
import websockets
import logging
import sys
from fog05.DStore import *


# The commands accepted by this server have the format:
#     command store-id arg1 arg2 ... argn
# where the command represents the method to execute on the given store-id and the args are the
# arguments for the command.

class Server (object):
    def __init__(self, port):
        self.port = port
        self.svc = None

        self.logger_impl = logging.getLogger('websockets')
        self.logger_impl.setLevel(logging.DEBUG)
        self.logger_impl.addHandler(logging.StreamHandler())
        # self.logger = DLogger()
        # self.logger.logger = self.logger_impl
        self.sessionMap= {}

    async def process(self, websocket, cmd):
        if cmd is not None:
            xs = [x for x in cmd.split(' ') if x is not '']
            if len(xs) < 2:
                print(">> Received invalid command {}".format(str(cmd)))
            else:
                cid = xs[0]
                sid = xs[1]
                args = xs[2:]
                await self.handle_command(websocket, cid, sid, args)


    def create_store(self, sid, args):
        if len(args) < 3:
            return None
        else:
            return DStore(sid, args[0], args[1], int(args[2]))

    def put(self, store, args):
        if len(args) < 2:
            return False
        else:
            store.put(args[0], args[1])
            return True

    def get(self, store, args):
        v = ''
        if len(args) > 0:
            v = store.get(args[0])
            if v is None:
                v = ''
            return v

    async def send_error(self, websocket, val):
        await websocket.send("NOK {}".format(val))

    async def send_success(self, websocket, val):
        await websocket.send("OK ".format(val))

    async def handle_command(self, websocket, cid, sid, args):
        # self.logger.debug("fog05ws", ">> Handling command {}".format(cid))
        print(">> Handling command {}".format(cid))

        raddr = str(websocket.remote_address)
        session = {}
        if raddr in self.sessionMap.keys():
            session = self.sessionMap[raddr]
        else:
            self.sessionMap[raddr] = session

        # -- Create
        if cid == 'create':
            if not (sid in session.keys()):
                s = self.create_store(sid, args)
                if s is None:
                    self.send_error(websocket, cid)
                else:
                    self.send_success(websocket, cid)

        # -- Put
        elif cid == 'put':
            if sid in session.keys():
                store = session.get(sid)
                self.put(store, args)
                self.send_success(cid)
            else:
                self.send_error(cid)

        elif cid == 'get':
            if sid in session.keys():
                store = session.get(sid)
                v = self.get(store, args)
                self.send_success("{} {} {}".format(cid, args[0], v))
            else:
                self.send_error(cid)

        await websocket.send("Command Executed")

    async def dispatch(self, websocket, path):
        while True:
            raddr = websocket.remote_address
            print("Connection from: {}".format(raddr))
            async for message in websocket:
                # self.logger.error("fog05ws", ">> Processing message {}".format(message))
                print(">> Processing message {}".format(message))
                await self.process(websocket, message)

            print(">> Peer closed the connection.")
            websocket.close()
            break


    def start(self):
        if self.svc is None:
            # self.logger.info("fog05ws", ">> fog05 web-socket service is listening on port {}".format(self.port))
            print(">> fog05 web-socket service is listening on port {}".format(self.port))
            self.svc = websockets.serve(self.dispatch, 'localhost', self.port)
            asyncio.get_event_loop().run_until_complete(self.svc)
            asyncio.get_event_loop().run_forever()
        else:
            raise RuntimeError("Service Already Running")


if __name__=='__main__':
    port = 9669
    if len(sys.argv) > 1:
        port = int(sys.argv)

    s = Server(port)
    s.start()