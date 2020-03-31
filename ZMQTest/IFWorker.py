import zmq
from zmq.eventloop.zmqstream import ZMQStream
from tornado.ioloop import IOLoop
from IFCore import IFException, Message, Invocation, IFLoop, IFDefinition
import time
import threading


class IFWorker(object):
    def __init__(self, endpoint, serviceName=None, serviceObject=None, interfaces=[], blocking=True, timeout=None):
        self.__endpoint = endpoint
        socket = zmq.Context().socket(zmq.DEALER)
        self.__stream = ZMQStream(socket, IOLoop.current())
        self.__stream.on_recv(self.__onMessage)
        self.__stream.socket.setsockopt(zmq.LINGER, 0)
        self.__stream.connect(self.__endpoint)
        self.__waitingMap = {}
        self.__waitingMapLock = threading.Lock()
        self.blocking = blocking
        self.timeout = timeout
        self.__isService = serviceName != None
        self.__serviceName = serviceName
        self.__serviceObject = serviceObject
        self.__interfaces = interfaces
        threading.Thread(target=self.__hbLoop, daemon=True).start()
        IFLoop.tryStart()
        if self.__isService:
            self.registerAsService(self.__serviceName, self.__interfaces)

    def __hbLoop(self):
        while True:
            time.sleep(IFDefinition.HEARTBEAT_LIVETIME / 5)
            try:
                if not self.blockingInvoker(timeout=IFDefinition.HEARTBEAT_LIVETIME / 5).heartbeat() \
                        and self.__isService:
                    self.registerAsService(self.__serviceName, self.__interfaces)
            except BaseException as e:
                print('Heartbeat: {}'.format(e))

    def __onMessage(self, msg):
        try:
            # print('msg get: ', msg)
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
        # print('on req')
        # print(message)
        sourcePoint = message.fromAddress
        invocation = message.getInvocation()
        try:
            result = invocation.perform(self.__serviceObject)
            responseMessage = Message.newDirectMessage(sourcePoint, Invocation.newResponse(message.messageID, result))
            self.__stream.send_multipart(responseMessage.getContent())
        except BaseException as e:
            errorMsg = Message.newDirectMessage(sourcePoint, Invocation.newError(message.messageID, str(e)))
            self.__stream.send_multipart(errorMsg.getContent())

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
        self.__stream.send_multipart(msg.getContent())

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

    worker = IFWorker("tcp://127.0.0.1:25034", serviceObject=None, interfaces=['TestInterface 1', 'TestInterface 2'],
                      timeout=1)
    print(worker.listServiceNames())
