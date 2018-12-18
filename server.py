import asyncio
import json
import time
import random
import threading

def generate_json():
    data = {"timestamp": time.time()}
    for i in range(1, 11):
        data["float_" + str(i)] = random.random()
        data["int_" + str(i)] = random.randint(0, 1)
    return json.dumps(data)


class Server:
    __current_data = None
    __period = 1 / 30.
    __writer = None
    __writers = []

    def __init__(self):
        self.__writers_lock = threading.Lock()

    async def generate_data(self):
        while True:
            await asyncio.sleep(self.__period)
            self.__current_data = generate_json()
            self.__writers_lock.acquire()
            if len(self.__writers) > 0:
                for w in self.__writers:
                    w.write(self.__current_data.encode())
                    await w.drain()
            self.__writers_lock.release()
            # if self.__writer is not None:
            #     if not self.__writer.is_closing():
            #         self.__writer.write(self.__current_data.encode())
            #         await self.__writer.drain()

    async def handle_client(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        print("Received %r from %r" % (message, addr))

        self.__writers.append(writer)
        self.__writer = writer
        request = None
        while request != 'quit':
            try:
                request = await reader.read(100)
                if len(request.decode()) > 0:
                    print("Request from", addr, request.decode())
                    request = request.decode()
            except ConnectionResetError:
                print("Connection with", addr, "lost")
                request = 'quit'
        self.__writer = None
        self.__writers_lock.acquire()
        self.__writers.remove(writer)
        self.__writers_lock.release()
        writer.close()
        print("Connection with", addr, "closed")

    def run(self):
        loop = asyncio.get_event_loop()
        coro = asyncio.start_server(self.handle_client, '127.0.0.1', 8888, loop=loop)
        print("Server started")
        loop.run_until_complete(asyncio.gather(coro, self.generate_data()))
        loop.close()


if __name__ == "__main__":
    server = Server()
    server.run()
