import asyncio
import websockets
import sys


async def hello(ws):
    async with websockets.connect('ws://{}:9669'.format(ws)) as websocket:
        while True:
            cmd = input(">>>  ")
            if cmd is '0':
                print("Closing Session. Ciao!")
                websocket.close()
                break
            await websocket.send(cmd)
            response = await websocket.recv()
            print("{}".format(response))
            xs = cmd.split(' ')
            if len(xs) > 0 and xs[0] == 'observe':
                while True:
                    response = await websocket.recv()
                    print("{}".format(response))

if __name__ == '__main__':

    asyncio.get_event_loop().run_until_complete(hello(sys.argv[1]))
