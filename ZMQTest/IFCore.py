__license__ = "GNU General Public License v3"
__author__ = 'Hwaipy'
__email__ = 'hwaipy@gmail.com'

import threading
import msgpack
import re
from tornado.ioloop import IOLoop
from threading import Thread


class IFDefinition:
    PROTOCOL = b'IF1'
    DISTRIBUTING_MODE_BROKER = b'Broker'
    DISTRIBUTING_MODE_DIRECT = b'Direct'
    DISTRIBUTING_MODE_SERVICE = b'Service'


class IFException(Exception):
    def __init__(self, description):
        Exception.__init__(self)
        self.description = description

    def __str__(self):
        return self.description


class IFLoop:
    __loopLock = threading.Lock()
    __running = False
    __loopingThread = None

    @classmethod
    def start(cls, background=True):
        if not IFLoop.__runIfNot(): raise IFException('IFLoop is already running.')
        if background:
            thread = Thread(target=IOLoop.current().start)
            thread.setDaemon(True)
            thread.start()
            IFLoop.__loopingThread = thread
        else:
            IFLoop.__loopingThread = threading.current_thread()
            IOLoop.current().start()

    @classmethod
    def tryStart(cls):
        if IFLoop.__runIfNot():
            thread = Thread(target=IOLoop.current().start)
            thread.setDaemon(True)
            thread.start()
            IFLoop.__loopingThread = thread

    @classmethod
    def __runIfNot(cls):
        IFLoop.__loopLock.acquire()
        if IFLoop.__running:
            IFLoop.__loopLock.release()
            return False
        IFLoop.__running = True
        IFLoop.__loopLock.release()
        return True

    @classmethod
    def join(cls):
        IFLoop.__loopingThread.join()

class Message:
    MessageIDs = 0

    @classmethod
    def newBrokerMessage(cls, invocation, serialization='Msgpack'):
        return Message.newMessage(IFDefinition.DISTRIBUTING_MODE_BROKER, b'', invocation, serialization)

    @classmethod
    def newServiceMessage(cls, serviceName, invocation, serialization='Msgpack'):
        return Message.newMessage(IFDefinition.DISTRIBUTING_MODE_SERVICE, serviceName, invocation, serialization)

    @classmethod
    def newMessage(cls, distributingMode, distributingAddress, invocation, serialization='Msgpack'):
        if (distributingMode != IFDefinition.DISTRIBUTING_MODE_BROKER) and (
                distributingMode != IFDefinition.DISTRIBUTING_MODE_DIRECT) and (
                distributingMode != IFDefinition.DISTRIBUTING_MODE_SERVICE): raise IFException(
            'Bad DistributingMode: {}'.format(distributingMode))
        if distributingMode == IFDefinition.DISTRIBUTING_MODE_BROKER: distributingAddress = b''
        # if serialization == 'Plain' or serialization == 'Default' or serialization == 'ZMQ': serialization = b''
        id = Message.__getAndIncrementID()
        id = msgpack.packb(id)
        msg = [b'', IFDefinition.PROTOCOL, id, distributingMode, distributingAddress,
               serialization, invocation.serialize(serialization)]
        return Message([Message.__messagePartToBytes(m) for m in msg])

    @classmethod
    def newFromBrokerMessage(cls, fromAddress, invocation, serialization='Msgpack'):
        id = Message.__getAndIncrementID()
        id = msgpack.packb(id)
        msg = [b'', IFDefinition.PROTOCOL, id, fromAddress, serialization, invocation.serialize(serialization)]
        return [Message.__messagePartToBytes(m) for m in msg]

    @classmethod
    def __getAndIncrementID(cls):
        __mutex__ = threading.Lock()
        __mutex__.acquire()
        id = Message.MessageIDs
        Message.MessageIDs += 1
        __mutex__.release()
        return id

    @classmethod
    def __messagePartToBytes(self, p):
        if isinstance(p, bytes): return p
        if isinstance(p, str): return bytes(p, 'UTF-8')
        if p == None: return b''
        raise IFException('Data type not transportable: {}'.format(type(p)))

    def __init__(self, msgc):
        self.__content = msgc
        self.__protocol = msgc[1]
        self.messageID = msgc[2]
        if self.isOutgoingMessage():
            self.__distributingMode = msgc[3]
            self.distributingAddress = msgc[4]
            self.serialization = msgc[5]
            self.__invocationContent = msgc[6]
        else:
            self.__distributingMode = b'Received'
            self.fromAddress = msgc[3]
            self.serialization = msgc[4]
            self.__invocationContent = msgc[5]
        self.__invocation = None

    def isProtocolValid(self):
        return self.__protocol == IFDefinition.PROTOCOL

    def isOutgoingMessage(self):
        return len(self.__content) == 7

    def isBrokerMessage(self):
        return self.isOutgoingMessage() and self.__distributingMode == IFDefinition.DISTRIBUTING_MODE_BROKER

    def isServiceMessage(self):
        return self.isOutgoingMessage() and self.__distributingMode == IFDefinition.DISTRIBUTING_MODE_SERVICE

    def isDirectMessage(self):
        return self.isOutgoingMessage() and self.__distributingMode == IFDefinition.DISTRIBUTING_MODE_DIRECT

    def getInvocation(self, decoded=True):
        if not decoded:
            return self.__invocationContent
        if not self.__invocation:
            self.__invocation = Invocation.deserialize(self.__invocationContent, self.serialization)
        return self.__invocation

    def getContent(self):
        return self.__content

    def __str__(self):
        if self.isBrokerMessage():
            return 'Broker: [id={}] {}'.format(self.messageID, self.getInvocation())
        if self.isServiceMessage():
            return 'Service [{}]: [id={}] {}'.format(self.distributingAddress, self.messageID, self.getInvocation())
        if self.isDirectMessage():
            return 'Direct [{}]: [id={}] {}'.format(self.distributingAddress, self.messageID, self.getInvocation())
        else:
            return 'Receive from [{}]: [id={}] {}'.format('Broker' if self.fromAddress == b'' else self.fromAddress,
                                                          self.messageID, self.getInvocation())


class Invocation:
    KeyType = u'Type'
    KeyFunciton = u'Function'
    KeyArguments = u'Arguments'
    KeyKeyworkArguments = u'KeyworkArguments'
    KeyRespopnseID = u'RespopnseID'
    KeyResult = u'Result'
    KeyError = u'Error'
    KeyWarning = u'Warning'
    ValueTypeRequest = u'Request'
    ValueTypeResponse = u'Response'
    Preserved = [KeyType, KeyFunciton, KeyArguments, KeyKeyworkArguments, KeyRespopnseID, KeyResult, KeyError,
                 KeyWarning]

    def __init__(self, content={}):
        self.__content = content

    def get(self, key, nilValid=True, nonKeyValid=True):
        if self.__content.__contains__(key):
            value = self.__content[key]
            if value == None:
                if nilValid:
                    return None
                else:
                    raise IFException("Nil value invalid with key {}.".format(key))
            else:
                return value
        elif (nonKeyValid):
            return None
        else:
            raise IFException("Invocation does not contains key {}.".format(key))

    def isRequest(self):
        return self.get(Invocation.KeyType) == Invocation.ValueTypeRequest

    def isResponse(self):
        return self.get(Invocation.KeyType) == Invocation.ValueTypeResponse

    def isError(self):
        return self.isResponse() and self.__content.__contains__(Invocation.KeyError)

    def hasWarning(self):
        return self.isResponse() and self.__content.__contains__(Invocation.KeyWarning)

    def getResponseID(self):
        if self.isResponse(): return self.get(Invocation.KeyRespopnseID)
        return None

    def getResult(self):
        if self.isResponse() and not self.isError():
            return self.get(Invocation.KeyResult)
        return None

    def getError(self):
        if self.isError(): return self.get(Invocation.KeyError)
        return None

    def getWarning(self):
        if self.isResponse(): return self.get(Invocation.KeyWarning)
        return None

    def getFunction(self):
        if self.isRequest():
            return self.get(Invocation.KeyFunciton)
        return None

    def getArguments(self):
        if self.isRequest():
            args = self.get(Invocation.KeyArguments)
            if args: return args if isinstance(args, list) else [args]
            return []
        return None

    def getKeywordArguments(self):
        if self.isRequest():
            kwargs = self.get(Invocation.KeyKeyworkArguments)
            return kwargs if kwargs else {}
        return None

    @classmethod
    def newRequest(cls, functionName, args, kwargs):
        return Invocation({
            Invocation.KeyType: Invocation.ValueTypeRequest,
            Invocation.KeyFunciton: functionName,
            Invocation.KeyArguments: args,
            Invocation.KeyKeyworkArguments: kwargs
        })

    @classmethod
    def newResponse(cls, messageID, result):
        return Invocation({
            Invocation.KeyType: Invocation.ValueTypeResponse,
            Invocation.KeyRespopnseID: messageID,
            Invocation.KeyResult: result
        })

    @classmethod
    def newError(cls, messageID, description):
        return Invocation({
            Invocation.KeyType: Invocation.ValueTypeResponse,
            Invocation.KeyRespopnseID: messageID,
            Invocation.KeyError: description
        })

    def serialize(self, serialization='Msgpack'):
        if serialization == 'Msgpack':
            return msgpack.packb(self.__content, use_bin_type=True)
        else:
            raise IFException('Bad serialization: {}'.format(serialization))

    def __str__(self):
        content = ', '.join(['{}: {}'.format(k, self.__content[k]) for k in self.__content.keys()])
        return "Invocation [{}]".format(content)

    @classmethod
    def deserialize(cls, bytes, serialization='Msgpack', contentOnly=False):
        if str(serialization, encoding='UTF-8') == 'Msgpack':
            unpacker = msgpack.Unpacker(raw=False)
            unpacker.feed(bytes)
            content = unpacker.__next__()
            return content if contentOnly else Invocation(content)
        else:
            raise IFException('Bad serialization: {}'.format(serialization))

    # sourcePoint only available for Broker.
    def perform(self, target, serialization, sourcePoint=None):
        try:
            method = getattr(target, self.getFunction())
        except BaseException as e:
            raise IFException('Function [{}] not available for Broker.'.format(self.getFunction()))
        if not callable(method):
            raise IFException('Function [{}] not available for Broker.'.format(self.getFunction()))
        args = self.getArguments()
        kwargs = self.getKeywordArguments()
        if sourcePoint:
            args = [sourcePoint] + args
        try:
            result = method(*args, **kwargs)
            return result
        except BaseException as e:
            matchEargs = re.search("takes ([0-9]+) positional arguments but ([0-9]+) were given", str(e))
            if matchEargs:
                minus = 2 if sourcePoint else 1
                raise IFException('Function [{}] expects [{}] arguments, but [{}] were given.'
                                  .format(self.getFunction(),
                                          int(matchEargs.group(1)) - minus,
                                          int(matchEargs.group(2)) - minus))
            matchEkwargs = re.search("got an unexpected keyword argument '(.+)'", str(e))
            if matchEkwargs:
                raise IFException(
                    'Keyword Argument [{}] not availabel for function [{}].'.format(matchEkwargs.group(1),
                                                                                    self.getFunction()))
            raise e

        # noResponse = message.get(Message.KeyNoResponse)
        # if callable(method):
        #     try:
        #         result = method(*args, **kwargs)
        #         response = message.response(result)
        #         if noResponse is not True:
        #             self.communicator.sendLater(response)
        #     except BaseException as e:
        #         error = message.error(e.__str__())
        #         self.communicator.sendLater(error)
        #     return

# class Session:

#     def start(self):
#         def hook(code, data):
#             if code == 11:
#                 return DynamicRemoteObject(self, False, True, str(data[:-8], 'utf-8'),
#                                            struct.unpack('!q', data[-8:])[0], 2)
#             else:
#                 raise IndexError()
#
#         self.unpacker = msgpack.Unpacker(encoding='utf-8', ext_hook=hook)
#
#         def createCommunicator():
#             sct = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             sct.connect(self.address)
#             self.socket = sct
#             self.communicator = Utils.BlockingCommunicator(self.socket, self.__dataFetcher, self.__dataSender)
#             self.communicator.start()
#             self.blockingInvoker().connect(self.name)
#
#         def waitCommunicatorToStop():
#             loopStepDuration = 0.3
#             pingDuration = 5
#             pingTimePast = 0
#             while True:
#                 time.sleep(loopStepDuration)
#                 if not self.communicator.isRunning():
#                     break
#                 pingTimePast += loopStepDuration
#                 if pingTimePast >= pingDuration:
#                     pingTimePast = 0
#                     try:
#                         self.blockingInvoker(timeout=5).ping()
#                     except Exception as e:
#                         return
#
#         def communicatorControlLoop():
#             while self.__running:
#                 if self.communicator.isRunning():
#                     waitCommunicatorToStop()
#                     if not self.__running:
#                         break
#                     print('Connection break. Try again.')
#                 try:
#                     createCommunicator()
#                 except BaseException as e:
#                     print('Can not Connect.')
#                 finally:
#                     time.sleep(5 + random.randint(1, 5000) / 1000.0)
#
#         createCommunicator()
#         threading.Thread(target=communicatorControlLoop, name="CommunicatorControlLoop").start()
#
#     def stop(self):
#         self.__running = False
#         self.communicator.stop()
#         self.socket.shutdown(socket.SHUT_RDWR)
#
#     def __sendMessage__(self, message):
#         class InvokeFuture:
#             @classmethod
#             def newFuture(cls):
#                 future = InvokeFuture()
#                 return (future, future.__onFinish, future.__resultMap)
#
#             def __init__(self):
#                 self.__done = False
#                 self.__result = None
#                 self.__exception = None
#                 self.__onComplete = None
#                 self.__metux = threading.Lock()
#                 self.__resultMap = {}
#                 self.__awaitSemaphore = threading.Semaphore(0)
#
#             def isDone(self):
#                 return self.__done
#
#             def isSuccess(self):
#                 return self.__exception is None
#
#             def result(self):
#                 return self.__result
#
#             def exception(self):
#                 return self.__exception
#
#             def onComplete(self, func):
#                 self.__metux.acquire()
#                 self.__onComplete = func
#                 if self.__done:
#                     self.__onComplete()
#                 self.__metux.release()
#
#             def waitFor(self, timeout=None):
#                 # For Python 3 only.
#                 # if self.__awaitSemaphore.acquire(True, timeout):
#                 #     self.__awaitSemaphore.release()
#                 #     return True
#                 # else:
#                 #     return False
#
#                 # For Python 2 & 3
#                 timeStep = 0.1 if timeout is None else timeout / 10
#                 startTime = time.time()
#                 while True:
#                     acq = self.__awaitSemaphore.acquire(False)
#                     if acq:
#                         return acq
#                     else:
#                         passedTime = time.time() - startTime
#                         if (timeout is not None) and (passedTime >= timeout):
#                             return False
#                         time.sleep(timeStep)
#
#             def sync(self, timeout=None):
#                 if self.waitFor(timeout):
#                     if self.isSuccess():
#                         return self.__result
#                     elif isinstance(self.__exception, BaseException):
#                         raise self.__exception
#                     else:
#                         raise ProtocolException('Error state in InvokeFuture.')
#                 else:
#                     raise ProtocolException('Time out!')
#
#             def __onFinish(self):
#                 self.__done = True
#                 if self.__resultMap.__contains__('result'):
#                     self.__result = self.__resultMap['result']
#                 if self.__resultMap.__contains__('error'):
#                     self.__exception = ProtocolException(self.__resultMap['error'])
#                 if self.__onComplete is not None:
#                     self.__onComplete()
#                 self.__awaitSemaphore.release()
#
#         id = message.messageID()
#         (future, onFinish, resultMap) = InvokeFuture.newFuture()
#         self.__waitingMapLock.acquire()
#         if self.__waitingMap.__contains__(id):
#             raise ProtocolException("MessageID have been used.")
#         self.__waitingMap[id] = (resultMap, onFinish)
#         self.__waitingMapLock.release()
#         self.communicator.sendLater(message)
#         return future
#
#     def __dataFetcher(self, socket):
#         try:
#             data = self.socket.recv(10000000)
#         except Exception as e:
#             print(e)
#             data = []
#         if len(data) == 0:
#             raise RuntimeError('Connection closed.')
#         self.unpacker.feed(data)
#         for packed in self.unpacker:
#             message = Message(packed)
#             self.__messageDeal(message)
#
#     def __dataSender(self, message):
#         mb = message.pack(self.__remoteObjectWarpper(message))
#         s = self.socket.send(mb)
#
#     def __messageDeal(self, message):
#         type = message.messageType()
#         if type is Message.Type.Request:
#             (name, args, kwargs) = message.requestContent()
#             try:
#                 objectID = message.getObjectID()
#                 if objectID is None:
#                     objectID = 0
#                 if not self.__remoteReferenceKeyMap.__contains__(objectID):
#                     raise IndexError()
#                 invoker = self.__remoteReferenceKeyMap[objectID][0]
#                 # method = invoker.__getattribute__(name)
#                 method = getattr(invoker, name)
#                 noResponse = message.get(Message.KeyNoResponse)
#                 if callable(method):
#                     try:
#                         result = method(*args, **kwargs)
#                         response = message.response(result)
#                         if noResponse is not True:
#                             self.communicator.sendLater(response)
#                     except BaseException as e:
#                         error = message.error(e.__str__())
#                         self.communicator.sendLater(error)
#                     return
#             except BaseException as e:
#                 response = message.error('InvokeError: Command {} not found.'.format(name))
#                 self.communicator.sendLater(response)
#
#         elif (type is Message.Type.Response) or (type is Message.Type.Error):
#             if type is Message.Type.Response:
#                 (result, id) = message.responseContent()
#             else:
#                 (error, id) = message.errorContent()
#             self.__waitingMapLock.acquire()
#             if self.__waitingMap.__contains__(id):
#                 (futureEntry, runnable) = self.__waitingMap[id]
#                 if type is Message.Type.Response:
#                     futureEntry['result'] = result
#                 else:
#                     futureEntry['error'] = error
#                 runnable()
#             else:
#                 print('ResponseID not recognized: {}'.format(message))
#             self.__waitingMapLock.release()
#         else:
#             print('A Wrong Message: {}'.format(message))
#
#     def __remoteObjectWarpper(self, message):
#         def wrapper(obj):
#             target = message.getTo()
#             if isinstance(obj, RemoteObject):
#                 if (target is not None) and (obj.name == self.name):
#                     self._remoteObjectDistributed(obj.id, target)
#                 return obj
#             else:
#                 return self._instanceRemoteObject(obj, target)
#
#         return wrapper
#
#     def _instanceRemoteObject(self, obj, target=None):
#         with self.__remoteReferenceLock:
#             if self.__remoteReferenceMap.__contains__(obj):
#                 id = self.__remoteReferenceMap[obj]
#             else:
#                 id = self.__remoteReferenceID
#                 self.__remoteReferenceID += 1
#                 self.__remoteReferenceMap[obj] = id
#                 self.__remoteReferenceKeyMap[id] = (obj, {})
#             if target is not None:
#                 self._remoteObjectDistributed(id, target)
#             return RemoteObject(self.name, id)
#
#     def _remoteObjectDistributed(self, id, target):
#         with self.__waitingMapLock:
#             if self.__remoteReferenceKeyMap.__contains__(id):
#                 map = self.__remoteReferenceKeyMap[id][1]
#                 if map.__contains__(target):
#                     map[target] = map[target] + 1
#                 else:
#                     map[target] = 1
#
#     def _remoteObjectFinalized(self, id, target):
#         def fin(id, target):
#             if (self.__remoteReferenceKeyMap.__contains__(id)):
#                 (obj, i, map) = self.__remoteReferenceKeyMap[id]
#                 if map.__contains__(target):
#                     map[target] = map[target] - 1
#                     if map[target] is 0:
#                         map.__delitem__(target)
#                 if len(map) is 0:
#                     self.__remoteReferenceKeyMap.__delitem__(id)
#                     self.__remoteReferenceMap.__delitem__(obj)
#
#         with self.__remoteReferenceLock:
#             if id is None:
#                 [fin(key, target) for key in self.__remoteReferenceKeyMap.keys() if key > 0]
#             else:
#                 fin(id, target)


# class HttpSession:
#     def messageInvoker(self, target=None):
#         return DynamicRemoteObject(self, toMessage=True, blocking=False, target=target, objectID=0, timeout=None)
#
#     def asynchronousInvoker(self, target=None):
#         return DynamicRemoteObject(self, toMessage=False, blocking=False, target=target, objectID=0, timeout=None)
#
#     def blockingInvoker(self, target=None, timeout=None):
#         return DynamicRemoteObject(self, toMessage=False, blocking=True, target=target, objectID=0, timeout=timeout)
#
#     def __messageDeal(self, message):
#         type = message.messageType()
#         if type is Message.Type.Request:
#             (name, args, kwargs) = message.requestContent()
#             try:
#                 method = getattr(self.invoker, name)
#                 noResponse = message.get(Message.KeyNoResponse)
#                 if callable(method):
#                     try:
#                         result = method(*args, **kwargs)
#                         response = message.response(result)
#                         if noResponse is not True:
#                             self.__sendMessage__(response)
#                     except BaseException as e:
#                         error = message.error(e.__str__())
#                         self.__sendMessage__(error)
#                     return
#             except BaseException as e:
#                 response = message.error('InvokeError: Command {} not found.'.format(name))
#                 self.__sendMessage__(response)
#
#         elif (type is Message.Type.Response) or (type is Message.Type.Error):
#             if type is Message.Type.Response:
#                 (result, id) = message.responseContent()
#             else:
#                 (error, id) = message.errorContent()
#             self.__waitingMapLock.acquire()
#             if self.__waitingMap.__contains__(id):
#                 (futureEntry, runnable) = self.__waitingMap[id]
#                 if type is Message.Type.Response:
#                     futureEntry['result'] = result
#                 else:
#                     futureEntry['error'] = error
#                 runnable()
#             else:
#                 print('ResponseID not recognized: {}'.format(message))
#             self.__waitingMapLock.release()
#         else:
#             print('A Wrong Message: {}'.format(message))
#
