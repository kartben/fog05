import asyncio
import websockets

async def hello():
    async with websockets.connect('ws://localhost:9669') as websocket:
        while True:
            name = input("What's your name? ")
            if name is '0':
                print("> Closing Session")
                websocket.close()
                break
            await websocket.send(name)
            print("> {}".format(name))

            greeting = await websocket.recv()
            print("< {}".format(greeting))

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(hello())
