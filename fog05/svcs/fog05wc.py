import asyncio
import websockets

async def hello():
    async with websockets.connect('ws://localhost:9669') as websocket:
        while True:
            name = input(">>>  ")
            if name is '0':
                print("Closing Session. Ciao!")
                websocket.close()
                break
            await websocket.send(name)
            response = await websocket.recv()
            print("{}".format(response))

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(hello())
