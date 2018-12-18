import asyncio
import json
import re
from collections import namedtuple, deque
from json import JSONDecodeError

json_matcher = "\{.*?\}"


def match_json_from_corrupted_data(data):
    return re.findall(json_matcher, data)


async def tcp_echo_client(loop, msg_count):
    memory = deque(maxlen=100)
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888,
                                                   loop=loop)
    hello_message = "Server, " + str(msg_count) + " hi!"
    print('Send: %r' % hello_message)
    writer.write(hello_message.encode())

    is_open = True
    counter = 0
    try:
        while is_open and counter < msg_count:
            data = await reader.read(512)
            if data:
                counter += 1
                # print(data.decode())
                try:
                    x = json.loads(data, object_hook=lambda d: namedtuple('msg', d.keys())(*d.values()))
                    memory.append(x)
                except JSONDecodeError:
                    print("Error in", data)
                    jsons = match_json_from_corrupted_data(data.decode())
                    for j in jsons:
                        print("Json added")
                        x = json.loads(j, object_hook=lambda d: namedtuple('msg', d.keys())(*d.values()))
                        memory.append(x)

                # writer.write(str(counter).encode())
            else:
                is_open = False

    except KeyboardInterrupt:
        pass
    writer.write('quit'.encode())
    writer.close()

    print('Close the socket')


# message = 'Sashka, hi'
loop = asyncio.get_event_loop()
msg_counts = [18 * i for i in range(1, 21)]
tasks = [tcp_echo_client(loop, m) for m in msg_counts]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
