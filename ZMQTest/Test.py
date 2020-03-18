from IFCore import MDPBroker, MDPWorker
import zmq
from zmq.eventloop.ioloop import IOLoop
import threading
import time


class MyWorker(MDPWorker):
    HB_INTERVAL = 1000
    HB_LIVENESS = 3

    count = 0

    def on_request(self, msg):
        self.count = self.count + 1
        self.reply(msg)
        return


#
if __name__ == '__main__':
    context = zmq.Context()
    broker = MDPBroker(context, "tcp://127.0.0.1:5034")
    threading.Thread(target=IOLoop.instance().start).start()
    time.sleep(1)
    worker = MyWorker(context, "tcp://127.0.0.1:5034", b"echo")
