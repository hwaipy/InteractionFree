from ZMQTest.IFBroker import IFBroker
from ZMQTest.IFWorker import IFWorker
from ZMQTest.IFCore import IFLoop

if __name__ == '__main__':
    broker = IFBroker("tcp://127.0.0.1:25034")
    worker1 = IFWorker("tcp://127.0.0.1:25034", serviceName='TestService', serviceObject=None,
                       interfaces=['TestInterface 1', 'TestInterface 2'], timeout=1)
    worker2 = IFWorker("tcp://127.0.0.1:25034", serviceName='TestService2', serviceObject=None,
                       interfaces=['TestInterface 1', 'TestInterface 2'], timeout=1)
    worker3 = IFWorker("tcp://127.0.0.1:25034", serviceName='TestService3', serviceObject=None,
                       interfaces=['TestInterface 1', 'TestInterface 2'], timeout=1)
    IFLoop.join()
