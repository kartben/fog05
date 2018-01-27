import asyncio
import websockets
import sys

default_host = 'localhost'
default_port = 9669
async def repl(host, port):
    async with websockets.connect('ws://{}:{}'.format(host,port)) as websocket:
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
    host = default_host
    port = default_port

    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-help' or sys.argv[1] == '-h':
            print("\nUSAGE:\n\tpython3 fog05wc.py\n")
            exit(0)
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = sys.argv[2]

    asyncio.get_event_loop().run_until_complete(repl(host, port))
