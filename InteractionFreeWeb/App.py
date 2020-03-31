from tornado import websocket, web
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from tornado.ioloop import IOLoop
from IFBroker import IFBroker
from IFCore import IFLoop

class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("static/index.html")


class WebSocketHandler(websocket.WebSocketHandler):
    def open(self, *args, **kwargs):
        # print('open')
        self.currentMessage = []
        self.__endpoint = 'tcp://localhost:5034'
        socket = zmq.Context().socket(zmq.DEALER)
        self.__stream = ZMQStream(socket, IOLoop.current())
        self.__stream.on_recv(self.__onReceive)
        self.__stream.socket.setsockopt(zmq.LINGER, 0)
        self.__stream.connect(self.__endpoint)

    def on_close(self, *args, **kwargs):
        # print('close')
        pass

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


if __name__ == '__main__':
    broker = IFBroker('tcp://*:224')
    handlers_array = [(r'/', IndexHandler), (r'/ws', WebSocketHandler)]
    app = web.Application(handlers_array, debug=True, static_path='static')
    app.listen(8080)
    IFLoop.join()