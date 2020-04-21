import zmq
from zmq.eventloop.zmqstream import ZMQStream
from tornado.ioloop import IOLoop
from IFCore import IFException, Message, Invocation, IFLoop, IFDefinition
import time
import threading


class IFLocal:
    pass

if __name__ == '__main__':
    import threading
    import os