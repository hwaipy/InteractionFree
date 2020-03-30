__author__ = 'Hwaipy'

import sys
import unittest
import time
from IFBroker import IFBroker
from IFWorker import IFWorker
from IFCore import Message, IFException, IFLoop
from threading import Thread
from tornado.ioloop import IOLoop
import threading


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
        self.assertEqual(future1.exception().description, "Function [co] not available for Broker.")

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
            def v8(self): return "V8 great!"

            def v9(self): raise IFException("V9 not good.")

            def v10(self): raise IOError("V10 have problems.")

            def v(self, i, b): return "OK"

        worker1 = IFWorker(MessageTransportTest.brokerAddress, serviceObject=Target(), serviceName="T1-Benz")
        checker = IFWorker(MessageTransportTest.brokerAddress)
        benzChecker = checker.blockingInvoker("T1-Benz", 10)
        v8r = benzChecker.v8()

    #         self.assertEqual(v8r, "V8 great!")
    #         try:
    #             benzChecker.v9()
    #             self.assertTrue(False)
    #         except ProtocolException as e:
    #             self.assertEqual(e.__str__(), "V9 not good.")
    #         try:
    #             benzChecker.v10()
    #             self.assertTrue(False)
    #         except ProtocolException as e:
    #             self.assertEqual(e.__str__(), "V10 have problems.")
    #         self.assertEqual(benzChecker.v(1, False), "OK")
    #         try:
    #             benzChecker.v11()
    #             self.assertTrue(False)
    #         except ProtocolException as e:
    #             self.assertEqual(e.__str__(), "InvokeError: Command v11 not found.")
    #         mc1.stop()
    #         checker.stop()
    #
    #     def testClientNameDuplicated(self):
    #         mc1 = Session((MessageTransportTest.addr, MessageTransportTest.port), None, name="T2-ClientDuplicated")
    #         mc1.start()
    #         mc2 = Session((MessageTransportTest.addr, MessageTransportTest.port), None, name="T2-ClientDuplicated")
    #         self.assertRaises(ProtocolException, lambda: mc2.start())
    #         mc1.stop()
    #         time.sleep(0.5)
    #         mc2.blockingInvoker().connect(u"T2-ClientDuplicated")
    #         mc2.stop()
    #
    #     # def testInvokeAndReturnObject(self):
    #     #     class Target:
    #     #         class T:
    #     #             def change(self):
    #     #                 return 'Haha'
    #     #
    #     #         def func(self):
    #     #             return Target.T()
    #     #
    #     #     oc = Session.newSession((MessageTransportTest.addr, MessageTransportTest.port), Target(), "T3-Benz")
    #     #     checker = Session.newSession((MessageTransportTest.addr, MessageTransportTest.port), None, "T3-Checher")
    #     #     getter = checker.blockingInvoker(u"T3-Benz", 2)
    #     #     result = getter.func()
    #         # self.assertEqual(result.change(), 'Haha')
    #         # checker.stop()
    #         #
    #         # class Target2:
    #         #     def rGet(self):
    #         #         checker3 = Session.newSession((MessageTransportTest.addr, MessageTransportTest.port), None,
    #         #                                       "T3-Checher3")
    #         #         r = checker3.blockingInvoker("T3-Benz").func()
    #         #         checker3.stop()
    #         #         return r
    #         #
    #         # checker2 = Session.newSession((MessageTransportTest.addr, MessageTransportTest.port), Target2(), "T3-Checher2")
    #         # checker4 = Session.newSession((MessageTransportTest.addr, MessageTransportTest.port), None, "T3-Checher4")
    #         # getter2 = checker4.blockingInvoker("T3-Checher2")
    #         # self.assertEqual(getter2.rGet().name, 'T3-Benz')
    #         # checker2.stop()
    #         # checker4.stop()
    #         # oc.stop()
    #
    #     '''
    #   test("Test Session Listening") {
    #     val lc = MessageClient.newClient("localhost", port, "T5-Monitor")
    #     val latch = new CountDownLatch(2)
    #     lc.addSessionListener(new SessionListener {
    #       def sessionConnected(session: String) { latch.countDown }
    #       def sessionDisconnected(session: String) { latch.countDown }
    #     })
    #     val rc = MessageClient.newClient("localhost", port, "T5-Rabit")
    #     rc.stop.sync
    #     latch.await(2, java.util.concurrent.TimeUnit.SECONDS)
    #     lc.stop
    #   }
    # '''

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        time.sleep(1)
        IOLoop.current().stop()


if __name__ == '__main__':
    unittest.main()
