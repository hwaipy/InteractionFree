from tornado import websocket
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from tornado.ioloop import IOLoop
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
import msgpack
import json


class WebSocketZMQBridgeHandler(websocket.WebSocketHandler):
    def open(self, *args, **kwargs):
        self.currentMessage = []
        self.__endpoint = 'tcp://localhost:224'
        socket = zmq.Context().socket(zmq.DEALER)
        self.__stream = ZMQStream(socket, IOLoop.current())
        self.__stream.on_recv(self.__onReceive)
        self.__stream.socket.setsockopt(zmq.LINGER, 0)
        self.__stream.connect(self.__endpoint)

    def on_close(self, *args, **kwargs):
        print('close')
        self.__stream.close()

    def on_message(self, message):
        hasMore = message[0]
        self.currentMessage.append(message[1:])
        if not hasMore:
            sendingMessage = self.currentMessage
            self.currentMessage = []
            self.__stream.send_multipart(sendingMessage)

    def __onReceive(self, msg):
        for frame in msg[:-1]:
            self.write_message(b'\x01' + frame, binary=True)
        self.write_message(b'\x00' + msg[-1], binary=True)


# class ArduinoZMQBridgeOld(TCPServer):
#     async def handle_stream(self, stream, address):
#         def onReceive(msg):
#             msg[-2] = b'JSON'
#             doc = msgpack.unpackb(msg[-1], encoding='UTF-8')
#             if doc.__contains__('ResponseID'):
#                 doc['ResponseID'] = int(doc['ResponseID'])
#             msg[-1] = json.dumps(doc).encode('UTF-8')
#             print("ready to send back response. ", msg)
#             for frame in msg[:-1]:
#                 stream.write(bytes([len(frame) + 1]) + b'\x01' + frame)
#             stream.write(bytes([len(msg[-1]) + 1]) + b'\x00' + msg[-1])
#
#         currentMessage = []
#         endpoint = 'tcp://localhost:224'
#         socket = zmq.Context().socket(zmq.DEALER)
#         zmqStream = ZMQStream(socket, IOLoop.current())
#         zmqStream.on_recv(onReceive)
#         zmqStream.socket.setsockopt(zmq.LINGER, 0)
#         zmqStream.connect(endpoint)
#
#         # def on_message(message):
#         #     hasMore = message[0]
#         #     currentMessage.append(message[1:])
#         #     if not hasMore:
#         #         sendingMessage = [m for m in currentMessage]
#         #         currentMessage.clear()
#         #         if len(sendingMessage) == 7:
#         #             sendingMessage[-2] = b'Msgpack'
#         #             print(sendingMessage[-1])
#         #             doc = json.loads(sendingMessage[-1])
#         #             sendingMessage[-1] = msgpack.packb(doc)
#         #             print('send a message a ZMQ server: ', sendingMessage)
#         #             zmqStream.send_multipart(sendingMessage)
#
#         def on_message(message):
#             hasMore = message[0]
#         #     currentMessage.append(message[1:])
#         #     if not hasMore:
#         #         sendingMessage = [m for m in currentMessage]
#         #         currentMessage.clear()
#         #         if len(sendingMessage) == 7:
#         #             sendingMessage[-2] = b'Msgpack'
#         #             print(sendingMessage[-1])
#         #             doc = json.loads(sendingMessage[-1])
#         #             sendingMessage[-1] = msgpack.packb(doc)
#         #             print('send a message a ZMQ server: ', sendingMessage)
#         #             zmqStream.send_multipart(sendingMessage)
#
#         errorCount = 0;
#         while True:
#             try:
#                 await stream.read_until(b'\xAE\xAE\xAE\xAE')
#                 data = await stream.read_until(b'\xAF\xAF\xAF\xAF')
#                 data = data[:-4]
#                 print(data)
#                 # size = await stream.read_bytes(1)
#                 # data = await stream.read_bytes(int(size[0]))
#                 # # print(data)
#                 # try:
#                 #     on_message(data)
#                 #     errorCount = 0
#                 # except RuntimeError as e:
#                 #     print('error. next.')
#                 #     errorCount += 1
#                 #     if errorCount == 100:
#                 #         print('100 errors. disconnect.')
#                 #         stream.close()
#             except StreamClosedError:
#                 break

class ArduinoZMQBridge(TCPServer):
    async def handle_stream(self, stream, address):
        def onReceive(msg):
            msg[-2] = b'JSON'
            doc = msgpack.unpackb(msg[-1], encoding='UTF-8')
            if doc.__contains__('ResponseID'):
                doc['ResponseID'] = int(doc['ResponseID'])
            msg[-1] = json.dumps(doc).encode('UTF-8')
            # print("ready to send to Arduino. ", msg)
            stream.write(b'\xAE\xAE\xAE\xAE')
            for frame in msg[:-1]:
                stream.write(bytes([len(frame) + 1]) + b'\x01' + frame)
            stream.write(bytes([len(msg[-1]) + 1]) + b'\x00' + msg[-1])
            stream.write(b'\xAF\xAF\xAF\xAF')

        endpoint = 'tcp://localhost:224'
        socket = zmq.Context().socket(zmq.DEALER)
        zmqStream = ZMQStream(socket, IOLoop.current())
        zmqStream.on_recv(onReceive)
        zmqStream.socket.setsockopt(zmq.LINGER, 0)
        zmqStream.connect(endpoint)

        def on_message(message):
            frames = []
            position = 0
            while True:
                if len(message) <= position: break
                size = message[position]
                if len(message) < position + size + 1: raise RuntimeError("Invalid Frame.")
                frames.append(message[position + 2:position + size + 1])
                position += size + 1
            if len(frames) != 7: raise RuntimeError("Bad Frame.")
            if len(frames[0]) != 0: raise RuntimeError("Bad Frame 0.")
            if frames[1] != b'IF1': raise RuntimeError("Bad Protocol.")
            if frames[3] != b'Broker' and frames[3] != b'Service' and frames[3] != b'Direct': raise RuntimeError("Bad Distributing Mode.")
            frames[-2] = b'Msgpack'
            doc = json.loads(frames[-1])
            frames[-1] = msgpack.packb(doc)
            # print('send a message a ZMQ server: ', frames)
            zmqStream.send_multipart(frames)

        errorCount = 0;
        while True:
            try:
                await stream.read_until(b'\xAE\xAE\xAE\xAE')
                data = await stream.read_until(b'\xAF\xAF\xAF\xAF')
                data = data[:-4]
                on_message(data)
            except StreamClosedError:
                print('closed')
                break
            except RuntimeError as e:
                print(e)

    @classmethod
    def start(cls):
        server = ArduinoZMQBridge()
        server.listen(228)
