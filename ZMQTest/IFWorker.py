import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import DelayedCallback, PeriodicCallback
from tornado.ioloop import IOLoop
from IFCore import IFDefinition, IFException, Message, Invocation


class IFWorker(object):
    # HB_INTERVAL = 1000  # in milliseconds
    # HB_LIVENESS = 3  # HBs to miss before connection counts as dead

    def __init__(self, endpoint):
        self.endpoint = endpoint
        socket = zmq.Context().socket(zmq.DEALER)
        self.stream = ZMQStream(socket, IOLoop.current())
        self.stream.on_recv(self.__onMessage)
        self.stream.socket.setsockopt(zmq.LINGER, 0)
        self.stream.connect(self.endpoint)

        print(self.registerAs('First Service'))
        # print(self.blockingInvoker('target').function(1, 2, yes='no'))
        # registerMsg = Message.newBrokerMessage(None)
        # [b'', IFDefinition.PROTOCOL, IFDefinition.DISTRIBUTING_MODE_BROKER, b'', 'Register', 'TestWorkerService']
        # self.__send(registerMsg)
        #     self.curr_liveness = self.HB_LIVENESS
        #
        # self.stream = None
        # self._tmo = None
        # self.need_handshake = True
        # self.ticker = None
        # self._delayed_cb = None
        # self.ticker = PeriodicCallback(self._tick, self.HB_INTERVAL)
        # self._send_ready()
        # self.ticker.start()

    def __onMessage(self, msg):
        print('msg get: {}'.format(msg))
        pass

    def send(self, msg):
        print('sending: {}'.format(msg))
        self.stream.send_multipart(msg)

    def toMessageInvoker(self, target=None):
        return DynamicRemoteObject(None, toMessage=True, blocking=False, target=target, timeout=None)

    def asynchronousInvoker(self, target=None):
        return DynamicRemoteObject(self, toMessage=False, blocking=False, target=target, timeout=None)

    def blockingInvoker(self, target=None, timeout=None):
        return DynamicRemoteObject(self, toMessage=False, blocking=True, target=target, timeout=timeout)

    @classmethod
    def start(cls):
        IOLoop.current().start()

    def __getattr__(self, item):
        return InvokeTarget(self, item)


class InvokeTarget:
    def __init__(self, worker, item):
        self.worker = worker
        self.name = item

    def __getattr__(self, item):
        item = u'{}'.format(item)
        return self.worker.blockingInvoker(self.name, self.worker.defaultblockingInvokerTimeout).__getattr__(item)

    def __call__(self, *args, **kwargs):
        invoker = self.worker.blockingInvoker('', self.worker.defaultblockingInvokerTimeout)
        func = invoker.__getattr__(self.name)
        return func(*args, **kwargs)


class RemoteObject(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "RemoteObject[{}]".format(self.name)


class DynamicRemoteObject(RemoteObject):
    def __init__(self, worker, toMessage, blocking, target, timeout):
        super(DynamicRemoteObject, self).__init__(target)
        self.__worker = worker
        self.__target = target
        self.__toMessage = toMessage
        self.__blocking = blocking
        self.__timeout = timeout
        self.name = target

    def __getattr__(self, item):
        item = u'{}'.format(item)

        def invoke(*args, **kwargs):
            invocation = Invocation.newRequest(item, args, kwargs)
            if self.__target == '':
                message = Message.newBrokerMessage(invocation)
            else:
                message = Message.newServiceMessage(self.__target, invocation)
            if self.__toMessage:
                return message
            elif self.__blocking:
                return self.__worker.send(message)  # .sync(self.__timeout)
            else:
                return self.__session.__send(message)

        return invoke

    def __str__(self):
        return "DynamicRemoteObject[{}]".format(self.name)


if __name__ == '__main__':
    import threading

    worker = IFWorker("tcp://127.0.0.1:5034")

    IFWorker.start()
    worker.shutdown()

    # def _tick(self):
    #     """Method called every HB_INTERVAL milliseconds.
    #     """
    #     self.curr_liveness -= 1
    #     ##         print '%.3f tick - %d' % (time.time(), self.curr_liveness)
    #     self.send_hb()
    #     if self.curr_liveness >= 0:
    #         return
    #     ## print '%.3f lost connection' % time.time()
    #     # ouch, connection seems to be dead
    #     self.shutdown()
    #     # try to recreate it
    #     self._delayed_cb = DelayedCallback(self._create_stream, 5000)
    #     self._delayed_cb.start()
    #     return
    #
    # def send_hb(self):
    #     """Construct and send HB message to broker.
    #     """
    #     msg = [b'', self._proto_version, b'\x04']
    #     self.stream.send_multipart(msg)
    #     return
    #
    # def shutdown(self):
    #     """Method to deactivate the worker connection completely.
    #
    #     Will delete the stream and the underlying socket.
    #     """
    #     if self.ticker:
    #         self.ticker.stop()
    #         self.ticker = None
    #     if not self.stream:
    #         return
    #     self.stream.socket.close()
    #     self.stream.close()
    #     self.stream = None
    #     self.timed_out = False
    #     self.need_handshake = True
    #     self.connected = False
    #     return
    #
    # def reply(self, msg):
    #     """Send the given message.
    #
    #     msg can either be a byte-string or a list of byte-strings.
    #     """
    #     ##         if self.need_handshake:
    #     ##             raise ConnectionNotReadyError()
    #     # prepare full message
    #     to_send = self.envelope
    #     self.envelope = None
    #     if isinstance(msg, list):
    #         to_send.extend(msg)
    #     else:
    #         to_send.append(msg)
    #     self.stream.send_multipart(to_send)
    #     return
    #
    # def _on_message(self, msg):
    #     """Helper method called on message receive.
    #
    #     msg is a list w/ the message parts
    #     """
    #     # 1st part is empty
    #     msg.pop(0)
    #     # 2nd part is protocol version
    #     # TODO: version check
    #     proto = msg.pop(0)
    #     # 3rd part is message type
    #     msg_type = msg.pop(0)
    #     # XXX: hardcoded message types!
    #     # any message resets the liveness counter
    #     self.need_handshake = False
    #     self.curr_liveness = self.HB_LIVENESS
    #     if msg_type == b'\x05':  # disconnect
    #         self.curr_liveness = 0  # reconnect will be triggered by hb timer
    #     elif msg_type == b'\x02':  # request
    #         # remaining parts are the user message
    #         envelope, msg = split_address(msg)
    #         envelope.append(b'')
    #         envelope = [b'', self._proto_version, b'\x03'] + envelope  # REPLY
    #         self.envelope = envelope
    #         self.on_request(msg)
    #     else:
    #         # invalid message
    #         # ignored
    #         pass
    #     return
    #
    # def on_request(self, msg):
    #     """Public method called when a request arrived.
    #
    #     Must be overloaded!
    #     """
    #     pass

# class ConnectionNotReadyError(RuntimeError):
#     """Exception raised when attempting to use the MDPWorker before the handshake took place.
#     """
#     pass
#
# class MissingHeartbeat(UserWarning):
#     """Exception raised when a heartbeat was not received on time.
#     """
#     pass
