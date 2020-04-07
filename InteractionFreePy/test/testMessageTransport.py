__author__ = 'Hwaipy'

import unittest
import time
from IFBroker import IFBroker
from IFWorker import IFWorker
from IFCore import Message, IFException
from tornado.ioloop import IOLoop
import threading
import asyncio
import queue


class MessageTransportTest(unittest.TestCase):
    testPort = 20111
    brokerAddress = 'tcp://127.0.0.1:{}'.format(testPort)

    @classmethod
    def setUpClass(cls):
        broker = IFBroker(MessageTransportTest.brokerAddress)

    def setUp(self):
        pass

    def testConnectionOfSession(self):
        worker = IFWorker(MessageTransportTest.brokerAddress)

    def testDynamicInvoker(self):
        worker = IFWorker(MessageTransportTest.brokerAddress)
        invoker = worker.toMessageInvoker()
        m1 = invoker.fun1(1, 2, "3", b=None, c=[1, 2, "3d"])
        self.assertTrue(m1.isProtocolValid())
        self.assertTrue(m1.isBrokerMessage())
        m1Invocation = m1.getInvocation()
        self.assertTrue(m1Invocation.isRequest())
        self.assertEqual(m1Invocation.getFunction(), 'fun1')
        self.assertEqual(m1Invocation.getArguments(), [1, 2, "3"])
        self.assertEqual(m1Invocation.getKeywordArguments(), {"b": None, "c": [1, 2, "3d"]})

        invoker2 = worker.toMessageInvoker("OnT")
        m2 = invoker2.fun2()
        m2Invocation = Message.getInvocation(m2)
        self.assertTrue(m2Invocation.isRequest())
        self.assertEqual(m2Invocation.getFunction(), 'fun2')
        self.assertEqual(m2Invocation.getArguments(), [])
        self.assertEqual(m2Invocation.getKeywordArguments(), {})
        self.assertTrue(m2.isServiceMessage())
        self.assertEqual(m2.distributingAddress, b'OnT')

    def testRemoteInvokeAndAsync(self):
        worker1 = IFWorker(MessageTransportTest.brokerAddress)
        invoker1 = worker1.asynchronousInvoker()
        future1 = invoker1.co()
        latch1 = threading.Semaphore(0)
        future1.onComplete(lambda: latch1.release())
        latch1.acquire()
        self.assertTrue(future1.isDone())
        self.assertFalse(future1.isSuccess())
        self.assertEqual(future1.exception().description, "Function [co] not available.")

        future1 = invoker1.protocol(a=1, b=2)
        latch1 = threading.Semaphore(0)
        future1.onComplete(lambda: latch1.release())
        latch1.acquire()
        self.assertTrue(future1.isDone())
        self.assertFalse(future1.isSuccess())
        self.assertEqual(future1.exception().description,
                         "Keyword Argument [a] not availabel for function [protocol].")
        future1 = invoker1.protocol(1, 2, 3)
        latch1 = threading.Semaphore(0)
        future1.onComplete(lambda: latch1.release())
        latch1.acquire()
        self.assertTrue(future1.isDone())
        self.assertFalse(future1.isSuccess())
        self.assertEqual(future1.exception().description,
                         "Function [protocol] expects [0] arguments, but [3] were given.")

    def testRemoteInvokeAndSync(self):
        worker = IFWorker(MessageTransportTest.brokerAddress)
        invoker = worker.blockingInvoker()
        self.assertRaises(IFException, lambda: invoker.co())
        self.assertEqual(invoker.protocol(), 'IF1')

    def testSyncAndAsyncMode(self):
        worker = IFWorker(MessageTransportTest.brokerAddress)
        self.assertRaises(IFException, lambda: worker.co())
        self.assertEqual(worker.protocol(), 'IF1')
        worker.blocking = False
        future1 = worker.protocol(1, 2, 3)
        latch1 = threading.Semaphore(0)
        future1.onComplete(lambda: latch1.release())
        latch1.acquire()
        self.assertTrue(future1.isDone())
        self.assertFalse(future1.isSuccess())
        self.assertEqual(future1.exception().description,
                         "Function [protocol] expects [0] arguments, but [3] were given.")

    def testInvokeOtherClient(self):
        class Target:
            def __init__(self):
                self.notFunction = 100

            def v8(self): return "V8 great!"

            def v9(self): raise IFException("V9 not good.")

            def v10(self): raise IOError("V10 have problems.")

            def v(self, i, b): return "OK"

        worker1 = IFWorker(MessageTransportTest.brokerAddress, serviceObject=Target(), serviceName="T1-Benz")
        checker = IFWorker(MessageTransportTest.brokerAddress)
        benzChecker = checker.blockingInvoker("T1-Benz", 1)
        v8r = benzChecker.v8()
        self.assertEqual(v8r, "V8 great!")
        try:
            benzChecker.v9()
            self.assertTrue(False)
        except IFException as e:
            self.assertEqual(e.__str__(), "V9 not good.")
        try:
            benzChecker.v10()
            self.assertTrue(False)
        except Exception as e:
            self.assertEqual(e.__str__(), "V10 have problems.")
        self.assertEqual(benzChecker.v(1, False), "OK")
        try:
            benzChecker.v11()
            self.assertTrue(False)
        except IFException as e:
            self.assertEqual(e.__str__(), "Function [v11] not available.")
        try:
            benzChecker.notFunction()
            self.assertTrue(False)
        except IFException as e:
            self.assertEqual(e.__str__(), "Function [notFunction] not available.")

    def testServiceDuplicated(self):
        worker1 = IFWorker(MessageTransportTest.brokerAddress, serviceName="T2-ClientDuplicated")
        try:
            worker2 = IFWorker(MessageTransportTest.brokerAddress, serviceName="T2-ClientDuplicated")
        except IFException as e:
            self.assertEqual(e.__str__(), "Service name [T2-ClientDuplicated] occupied.")

    # def testAsyncInvoke(self):
    #     class Target:
    #         def waitFor(self, timeToWait):
    #             time.sleep(timeToWait)
    #             return 'OK'
    #
    #     IFWorker(MessageTransportTest.brokerAddress, serviceName='DelayService', serviceObject=Target())
    #     worker1 = IFWorker(MessageTransportTest.brokerAddress, blocking=False, timeout=1.5)
    #
    #     batch = queue.Queue()
    #
    #     async def asyncInvokeTest():
    #         invoker = worker1.asynchronousInvoker('DelayService')
    #         print('123')
    #         try:
    #             result1 = invoker.waitFor()
    #         except BaseException as e:
    #             print(1, e)
    #         print(result1)
    #         # self.assertEqual(result1, 'OK')
    #         # result2 = await invoker.waitFor()
    #         time.sleep(2)
    #         print(await result1)
    #
    #         batch.put_nowait('')
    #
    #     asyncio.ensure_future(asyncInvokeTest())
    #     batch.get()

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        time.sleep(1)
        IOLoop.current().stop()


if __name__ == '__main__':
    unittest.main()
