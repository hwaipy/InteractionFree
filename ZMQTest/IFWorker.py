import zmq
from zmq.eventloop.zmqstream import ZMQStream
from tornado.ioloop import IOLoop
from IFCore import IFException, Message, Invocation, IFLoop
import time
import threading


class IFWorker(object):
    # HB_INTERVAL = 1000  # in milliseconds
    # HB_LIVENESS = 3  # HBs to miss before connection counts as dead

    def __init__(self, endpoint, blocking=True, timeout=None):
        self.endpoint = endpoint
        socket = zmq.Context().socket(zmq.DEALER)
        self.stream = ZMQStream(socket, IOLoop.current())
        self.stream.on_recv(self.__onMessage)
        self.stream.socket.setsockopt(zmq.LINGER, 0)
        self.stream.connect(self.endpoint)
        self.__waitingMap = {}
        self.__waitingMapLock = threading.Lock()
        self.blocking = blocking
        self.timeout = timeout

        # print(self.registerAs('First Service'))
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
        IFLoop.tryStart()

    def __onMessage(self, msg):
        try:
            message = Message(msg)
            # print('msg get: {}'.format(message))
            invocation = message.getInvocation()
            if invocation.isRequest():
                self.__onRequest(message)
            elif invocation.isResponse():
                self.__onResponse(message)
        except BaseException as e:
            import traceback
            exstr = traceback.format_exc()
            print(exstr)

    def __onRequest(self, message):
        raise RuntimeError('not imp')

        # (name, args, kwargs) = message.requestContent()
        # try:
        #     objectID = message.getObjectID()
        #     if objectID is None:
        #         objectID = 0
        #     if not self.__remoteReferenceKeyMap.__contains__(objectID):
        #         raise IndexError()
        #     invoker = self.__remoteReferenceKeyMap[objectID][0]
        #     # method = invoker.__getattribute__(name)
        #     method = getattr(invoker, name)
        #     noResponse = message.get(Message.KeyNoResponse)
        #     if callable(method):
        #         try:
        #             result = method(*args, **kwargs)
        #             response = message.response(result)
        #             if noResponse is not True:
        #                 self.communicator.sendLater(response)
        #         except BaseException as e:
        #             error = message.error(e.__str__())
        #             self.communicator.sendLater(error)
        #         return
        # except BaseException as e:
        #     response = message.error('InvokeError: Command {} not found.'.format(name))
        #     self.communicator.sendLater(response)

    def __onResponse(self, message):
        # print('get a response message: ', message)
        invocation = message.getInvocation()
        correspondingID = invocation.getResponseID()
        self.__waitingMapLock.acquire()
        if self.__waitingMap.__contains__(correspondingID):
            (futureEntry, runnable) = self.__waitingMap.pop(correspondingID)
            if invocation.isError():
                futureEntry['error'] = invocation.getError()
            else:
                futureEntry['result'] = invocation.getResult()
            if invocation.hasWarning():
                futureEntry['warning'] = invocation.getWarning()
            # print('ready to run')
            runnable()
        else:
            print('ResponseID not recognized: {}'.format(message))
        self.__waitingMapLock.release()

    def send(self, msg):
        # print('sending: {}'.format(msg))
        self.stream.send_multipart(msg.getContent())

        id = msg.messageID
        (future, onFinish, resultMap) = InvokeFuture.newFuture()
        self.__waitingMapLock.acquire()
        if self.__waitingMap.__contains__(id):
            raise IFException("MessageID have been used.")
        self.__waitingMap[id] = (resultMap, onFinish)
        self.__waitingMapLock.release()
        return future

    def toMessageInvoker(self, target=None):
        return DynamicRemoteObject(None, toMessage=True, blocking=False, target=target, timeout=None)

    def asynchronousInvoker(self, target=None):
        return DynamicRemoteObject(self, toMessage=False, blocking=False, target=target, timeout=None)

    def blockingInvoker(self, target=None, timeout=None):
        return DynamicRemoteObject(self, toMessage=False, blocking=True, target=target, timeout=timeout)

    @classmethod
    def start(cls):
        IOLoop.instance().start()

    def __getattr__(self, item):
        return InvokeTarget(self, item)


class InvokeTarget:
    def __init__(self, worker, item):
        self.__worker = worker
        self.__name = item

    def __getattr__(self, item):
        item = u'{}'.format(item)
        return self.__defaultInvoker(self.__name).__getattr__(item)

    def __call__(self, *args, **kwargs):
        invoker = self.__defaultInvoker('')
        func = invoker.__getattr__(self.__name)
        return func(*args, **kwargs)

    def __defaultInvoker(self, target):
        if self.__worker.blocking:
            return self.__worker.blockingInvoker(target, self.__worker.timeout)
        else:
            return self.__worker.asynchronousInvoker(target)


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
            if self.__target == '' or self.__target == None:
                message = Message.newBrokerMessage(invocation)
            else:
                message = Message.newServiceMessage(self.__target, invocation)
            if self.__toMessage:
                return message
            elif self.__blocking:
                return self.__worker.send(message).sync(self.__timeout)
            else:
                return self.__worker.send(message)

        return invoke

    def __str__(self):
        return "DynamicRemoteObject[{}]".format(self.name)


class InvokeFuture:
    @classmethod
    def newFuture(cls):
        future = InvokeFuture()
        return (future, future.__onFinish, future.__resultMap)

    def __init__(self):
        self.__done = False
        self.__result = None
        self.__exception = None
        self.__warning = None
        self.__onComplete = None
        self.__metux = threading.Lock()
        self.__resultMap = {}
        self.__awaitSemaphore = threading.Semaphore(0)

    def isDone(self):
        return self.__done

    def isSuccess(self):
        return self.__exception is None

    def result(self):
        return self.__result

    def exception(self):
        return self.__exception

    def warning(self):
        return self.__warning

    def onComplete(self, func):
        self.__metux.acquire()
        self.__onComplete = func
        if self.__done:
            self.__onComplete()
        self.__metux.release()

    def waitFor(self, timeout=None):
        # For Python 3 only.
        # if self.__awaitSemaphore.acquire(True, timeout):
        #     self.__awaitSemaphore.release()
        #     return True
        # else:
        #     return False

        # For Python 2 & 3
        timeStep = 0.1 if timeout is None else timeout / 10
        startTime = time.time()
        while True:
            acq = self.__awaitSemaphore.acquire(False)
            if acq:
                return acq
            else:
                passedTime = time.time() - startTime
                if (timeout is not None) and (passedTime >= timeout):
                    return False
                time.sleep(timeStep)

    def sync(self, timeout=None):
        if self.waitFor(timeout):
            if self.isSuccess():
                return self.__result
            elif isinstance(self.__exception, BaseException):
                raise self.__exception
            else:
                raise IFException('Error state in InvokeFuture.')
        else:
            raise IFException('Time out!')

    def __onFinish(self):
        self.__done = True
        if self.__resultMap.__contains__('result'):
            self.__result = self.__resultMap['result']
        if self.__resultMap.__contains__('warning'):
            self.__warning = self.__resultMap['warning']
        if self.__resultMap.__contains__('error'):
            self.__exception = IFException(self.__resultMap['error'])
        if self.__onComplete is not None:
            self.__onComplete()
        self.__awaitSemaphore.release()


if __name__ == '__main__':
    import threading
    import IFCore

    worker = IFWorker("tcp://127.0.0.1:5034", timeout=1)

    while True:
        time.sleep(1)
        try:
            print(worker.protocol())
        except BaseException as e:
            print(e)
    # worker.shutdown()

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
