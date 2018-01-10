import asyncio
import websockets
import logging
import sys
from fog05.DStore import *


# The commands accepted by this server have the format:
#     command store-id arg1 arg2 ... argn
# where the command represents the method to execute on the given store-id and the args are the
# arguments for the command.
#
# The commands currently supported are:
#
#    create  sid root home cache-size
#    close   sid
#
#    put     sid uri val
#    dput     sid uri [val]
#    get     sid uri
#    remove  sid uri
#
#    observe sid uri cookie


class Dispatcher (object):
    def __init__(self, cookie, wsock):
        self.cookie = cookie
        self.wsock = wsock


    def dispatch(self, key, val, ver):
        print("Dispatching observer")
        result = '{} {} {}'.format(self.cookie, key, val)
        asyncio.ensure_future(self.wsock.send(result))


class Server (object):
    def __init__(self, port):
        self.port = port
        self.svc = None

        self.logger_impl = logging.getLogger('websockets')
        self.logger_impl.setLevel(logging.DEBUG)
        self.logger_impl.addHandler(logging.StreamHandler())
        # self.logger = DLogger()
        # self.logger.logger = self.logger_impl
        self.storeMap = {}

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


    def create(self, sid, args):
        if len(args) < 3:
            return None
        else:
            return DStore(sid, args[0], args[1], int(args[2]))

    def close(self, sid):
        if sid in self.storeMap.keys():
            store = self.storeMap.pop(sid)
            store.close()

        return True

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

    def remove(self, store, args):
        if len(args) > 0:
            store.remove(args[0])
            return True
        else:
            return False

    def dput(self, store, args):
        result  = False
        if len(args) == 1:
            store.dput(args[0])
            result = True
        elif len(args) > 1:
            store.dput(args[0],args[1])
            result = True

        return result



    def observe(self, store, sid, args, websocket):
        success = False
        print("len(args) {}".format(len(args)))
        if len(args) > 1:
            success = True
            cookie = 'observe {} {}'.format(sid, args[1])
            disp = Dispatcher(cookie, websocket)
            store.observe(args[0], disp.dispatch)
        else:
            print("Observe failed!")
        print("success = {}".format(success))
        return success

    async def send_error(self, websocket, val):
        await websocket.send("NOK {}".format(val))

    async def send_success(self, websocket, val):
        await websocket.send("OK {}".format(val))


    async def handle_command(self, websocket, cid, sid, args):
        # self.logger.debug("fog05ws", ">> Handling command {}".format(cid))
        # print(">> Handling command {}".format(cid))

        result = cid
        success = False

        # -- Create
        if cid == 'create':
            if not (sid in self.storeMap.keys()):
                s = self.create(sid, args)
                if s is not None:
                    self.storeMap[sid] = s
                    success = True

        elif cid == 'close':
            success = self.close(sid)

        else:
            store = None
            if sid in self.storeMap.keys():
                store = self.storeMap.get(sid)

                # -- Put
                if cid == 'put':
                    if self.put(store, args):
                        result = "{} {} {}".format(cid, sid, args[0])
                        success = True

                # -- DPut
                if cid == 'dput':
                    if self.dput(store, args):
                        result = "{} {} {}".format(cid, sid, args[0])
                        success = True

                # -- Remove
                if cid == 'remove':
                    if self.removet(store, args):
                        result = "{} {} {}".format(cid, sid, args[0])
                        success = True

                # -- Get
                elif cid == 'get':
                    v = self.get(store, args)
                    result = "{} {} {} {}".format(cid, sid, args[0], v)
                    success = True

                # -- Observe
                elif cid == 'observe':
                    if self.observe(store, sid, args, websocket):
                        result = "{} {} {}".format(cid, args[0], args[1])
                        success = True


        if success:
            await self.send_success(websocket, result)
        else:
            await self.send_error(websocket, result)

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
            self.svc = websockets.serve(self.dispatch, '0.0.0.0', self.port)
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