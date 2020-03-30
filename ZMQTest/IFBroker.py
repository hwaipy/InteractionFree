__license__ = "GNU General Public License v3"
__author__ = 'Hwaipy'
__email__ = 'hwaipy@gmail.com'

import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import PeriodicCallback
from IFCore import IFDefinition, IFException, Invocation, Message, IFLoop
from tornado.ioloop import IOLoop


class IFBroker(object):
    def __init__(self, binding):
        socket = zmq.Context().socket(zmq.ROUTER)
        socket.bind(binding)
        self.main_stream = ZMQStream(socket, IOLoop.current())
        self.main_stream.on_recv(self.__onMessage)
        self.manager = Manager(self)
        IFLoop.tryStart()

    def close(self):
        self.main_stream.on_recv(None)
        self.main_stream.socket.setsockopt(zmq.LINGER, 0)
        self.main_stream.socket.close()
        self.main_stream.close()
        self.main_stream = None

    def __onMessage(self, msg):
        sourcePoint, msg = msg[0], msg[1:]
        protocol = msg[1]
        if protocol != IFDefinition.PROTOCOL: raise IFException('Protocol {} not supported.'.format(protocol))
        distributingMode = msg[3]
        if distributingMode == IFDefinition.DISTRIBUTING_MODE_BROKER:
            self.__onMessageDistributeLocal(sourcePoint, msg)
        elif distributingMode == IFDefinition.DISTRIBUTING_MODE_DIRECT:
            self.__onMessageDistributeDirect(sourcePoint, msg)
        elif distributingMode == IFDefinition.DISTRIBUTING_MODE_SERVICE:
            self.__onMessageDistributeService(sourcePoint, msg)
        else:
            raise IFException('Distributing mode {} not supported.'.format(distributingMode))

    def __onMessageDistributeLocal(self, sourcePoint, msg):
        try:
            message = Message(msg)
            invocation = message.getInvocation()
            result = invocation.perform(self.manager, message.serialization, sourcePoint)
            responseMessage = Message.newFromBrokerMessage(b'', Invocation.newResponse(message.messageID, result))
            self.main_stream.send_multipart([sourcePoint] + responseMessage)
        except BaseException as e:
            errorMsg = Message.newFromBrokerMessage(b'', Invocation.newError(message.messageID, str(e)))
            self.main_stream.send_multipart([sourcePoint] + errorMsg)


class Manager:
    def __init__(self, broker):
        self.broker = broker
        # self.__workers = []
        self.__services = {}

    def registerAsService(self, sourcePoint, name, interfaces=[]):
        if self.__services.__contains__(name):
            raise IFException('')
        print('registering')

    def protocol(self, sourcePoint):
        return str(IFDefinition.PROTOCOL, encoding='UTF-8')


if __name__ == '__main__':
    broker = IFBroker("tcp://127.0.0.1:5034")
    IFLoop.join()