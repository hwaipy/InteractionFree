__license__ = "GNU General Public License v3"
__author__ = 'Hwaipy'
__email__ = 'hwaipy@gmail.com'

import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import PeriodicCallback
from tornado.ioloop import IOLoop
from util import IFDefinition


# HB_INTERVAL = 1000  #: in milliseconds
# HB_LIVENESS = 5  #: HBs to miss before connection counts as dead

class IFBroker(object):
    def __init__(self, binding):
        socket = zmq.Context().socket(zmq.ROUTER)
        socket.bind(binding)
        self.main_stream = ZMQStream(socket)
        self.main_stream.on_recv(self.__onMessage)
        # self.client_stream = self.main_stream
        # self._workers = {}
        # self._services = {}
        # self._worker_cmds = {b'\x01': self.on_ready,
        #                      b'\x03': self.on_reply,
        #                      b'\x04': self.on_heartbeat,
        #                      b'\x05': self.on_disconnect,
        #                      }
        # self.hb_check_timer = PeriodicCallback(self.on_timer, HB_INTERVAL)
        # self.hb_check_timer.start()

    def __onMessage(self, msg):
        sourcePoint, msg = msg[0], msg[1:]

        f0 = msg.pop(0)
        # print(msg, ' from ', sourcePoint)
        protocol = str(msg.pop(0), 'UTF-8')
        if protocol != IFDefinition.PROTOCOL: raise RuntimeError('Protocol {} not supported.'.format(protocol))
        distributingMode = msg.pop(0)
        distributionAddress = msg.pop(0)
        if distributingMode == IFDefinition.DISTRIBUTING_MODE_BROKER:
            self.__onMessageDistributeLocal(msg)
        elif distributingMode == IFDefinition.DISTRIBUTING_MODE_DIRECT:
            self.__onMessageDistributeDirect(distributionAddress, msg)
        elif distributingMode == IFDefinition.DISTRIBUTING_MODE_SERVICE:
            self.__onMessageDistributeService(distributionAddress, msg)
        else:
            raise RuntimeError('Distributing mode {} not supported.'.format(distributingMode))

    def __onMessageDistributeLocal(self, msg):
        print('local')


if __name__ == '__main__':
    broker = IFBroker("tcp://127.0.0.1:5034")
    IOLoop.instance().start()
    # never reach here
    broker.shutdown()

    # def register_worker(self, wid, service):
    #     """Register the worker id and add it to the given service.
    #
    #     Does nothing if worker is already known.
    #
    #     :param wid:    the worker id.
    #     :type wid:     str
    #     :param service:    the service name.
    #     :type service:     str
    #
    #     :rtype: None
    #     """
    #     if wid in self._workers:
    #         return
    #     self._workers[wid] = WorkerRep(self.WORKER_PROTO, wid, service, self.main_stream)
    #     if service in self._services:
    #         wq, wr = self._services[service]
    #         wq.put(wid)
    #     else:
    #         q = ServiceQueue()
    #         q.put(wid)
    #         self._services[service] = (q, [])
    #     return
    #
    # def unregister_worker(self, wid):
    #     """Unregister the worker with the given id.
    #
    #     If the worker id is not registered, nothing happens.
    #
    #     Will stop all timers for the worker.
    #
    #     :param wid:    the worker id.
    #     :type wid:     str
    #
    #     :rtype: None
    #     """
    #     try:
    #         wrep = self._workers[wid]
    #     except KeyError:
    #         # not registered, ignore
    #         return
    #     wrep.shutdown()
    #     service = wrep.service
    #     if service in self._services:
    #         wq, wr = self._services[service]
    #         wq.remove(wid)
    #     del self._workers[wid]
    #     return
    #
    # def disconnect(self, wid):
    #     """Send disconnect command and unregister worker.
    #
    #     If the worker id is not registered, nothing happens.
    #
    #     :param wid:    the worker id.
    #     :type wid:     str
    #
    #     :rtype: None
    #     """
    #     try:
    #         wrep = self._workers[wid]
    #     except KeyError:
    #         # not registered, ignore
    #         return
    #     to_send = [wid, self.WORKER_PROTO, b'\x05']
    #     self.main_stream.send_multipart(to_send)
    #     self.unregister_worker(wid)
    #     return
    #
    # def client_response(self, rp, service, msg):
    #     """Package and send reply to client.
    #
    #     :param rp:       return address stack
    #     :type rp:        list of str
    #     :param service:  name of service
    #     :type service:   str
    #     :param msg:      message parts
    #     :type msg:       list of str
    #
    #     :rtype: None
    #     """
    #     to_send = rp[:]
    #     to_send.extend([b'', self.CLIENT_PROTO, service])
    #     to_send.extend(msg)
    #     self.client_stream.send_multipart(to_send)
    #     return
    #
    # def shutdown(self):
    #     """Shutdown broker.
    #
    #     Will unregister all workers, stop all timers and ignore all further
    #     messages.
    #
    #     .. warning:: The instance MUST not be used after :func:`shutdown` has been called.
    #
    #     :rtype: None
    #     """
    #     if self.client_stream == self.main_stream:
    #         self.client_stream = None
    #     self.main_stream.on_recv(None)
    #     self.main_stream.socket.setsockopt(zmq.LINGER, 0)
    #     self.main_stream.socket.close()
    #     self.main_stream.close()
    #     self.main_stream = None
    #     if self.client_stream:
    #         self.client_stream.on_recv(None)
    #         self.client_stream.socket.setsockopt(zmq.LINGER, 0)
    #         self.client_stream.socket.close()
    #         self.client_stream.close()
    #         self.client_stream = None
    #     self._workers = {}
    #     self._services = {}
    #     return
    #
    # def on_timer(self):
    #     """Method called on timer expiry.
    #
    #     Checks which workers are dead and unregisters them.
    #
    #     :rtype: None
    #     """
    #     for wrep in list(self._workers.values()):
    #         if not wrep.is_alive():
    #             self.unregister_worker(wrep.id)
    #     return
    #
    # def on_ready(self, rp, msg):
    #     """Process worker READY command.
    #
    #     Registers the worker for a service.
    #
    #     :param rp:  return address stack
    #     :type rp:   list of str
    #     :param msg: message parts
    #     :type msg:  list of str
    #
    #     :rtype: None
    #     """
    #     ret_id = rp[0]
    #     self.register_worker(ret_id, msg[0])
    #     return
    #
    # def on_reply(self, rp, msg):
    #     """Process worker REPLY command.
    #
    #     Route the `msg` to the client given by the address(es) in front of `msg`.
    #
    #     :param rp:  return address stack
    #     :type rp:   list of str
    #     :param msg: message parts
    #     :type msg:  list of str
    #
    #     :rtype: None
    #     """
    #     ret_id = rp[0]
    #     wrep = self._workers[ret_id]
    #     service = wrep.service
    #     # make worker available again
    #     try:
    #         wq, wr = self._services[service]
    #         cp, msg = split_address(msg)
    #         self.client_response(cp, service, msg)
    #         wq.put(wrep.id)
    #         if wr:
    #             proto, rp, msg = wr.pop(0)
    #             self.on_client(proto, rp, msg)
    #     except KeyError:
    #         # unknown service
    #         self.disconnect(ret_id)
    #     return
    #
    # def on_heartbeat(self, rp, msg):
    #     """Process worker HEARTBEAT command.
    #
    #     :param rp:  return address stack
    #     :type rp:   list of str
    #     :param msg: message parts
    #     :type msg:  list of str
    #
    #     :rtype: None
    #     """
    #     ret_id = rp[0]
    #     try:
    #         worker = self._workers[ret_id]
    #         if worker.is_alive():
    #             worker.on_heartbeat()
    #     except KeyError:
    #         # ignore HB for unknown worker
    #         pass
    #     return
    #
    # def on_disconnect(self, rp, msg):
    #     """Process worker DISCONNECT command.
    #
    #     Unregisters the worker who sent this message.
    #
    #     :param rp:  return address stack
    #     :type rp:   list of str
    #     :param msg: message parts
    #     :type msg:  list of str
    #
    #     :rtype: None
    #     """
    #     wid = rp[0]
    #     self.unregister_worker(wid)
    #     return
    #
    # def on_mmi(self, rp, service, msg):
    #     """Process MMI request.
    #
    #     For now only mmi.service is handled.
    #
    #     :param rp:      return address stack
    #     :type rp:       list of str
    #     :param service: the protocol id sent
    #     :type service:  str
    #     :param msg:     message parts
    #     :type msg:      list of str
    #
    #     :rtype: None
    #     """
    #     if service == b'mmi.service':
    #         s = msg[0]
    #         ret = b'404'
    #         for wr in list(self._workers.values()):
    #             if s == wr.service:
    #                 ret = b'200'
    #                 break
    #         self.client_response(rp, service, [ret])
    #     else:
    #         self.client_response(rp, service, [b'501'])
    #     return
    #
    # def on_client(self, proto, rp, msg):
    #     """Method called on client message.
    #
    #     Frame 0 of msg is the requested service.
    #     The remaining frames are the request to forward to the worker.
    #
    #     .. note::
    #
    #        If the service is unknown to the broker the message is
    #        ignored.
    #
    #     .. note::
    #
    #        If currently no worker is available for a known service,
    #        the message is queued for later delivery.
    #
    #     If a worker is available for the requested service, the
    #     message is repackaged and sent to the worker. The worker in
    #     question is removed from the pool of available workers.
    #
    #     If the service name starts with `mmi.`, the message is passed to
    #     the internal MMI_ handler.
    #
    #     .. _MMI: http://rfc.zeromq.org/spec:8
    #
    #     :param proto: the protocol id sent
    #     :type proto:  str
    #     :param rp:    return address stack
    #     :type rp:     list of str
    #     :param msg:   message parts
    #     :type msg:    list of str
    #
    #     :rtype: None
    #     """
    #     service = msg.pop(0)
    #     if service.startswith(b'mmi.'):
    #         self.on_mmi(rp, service, msg)
    #         return
    #     try:
    #         wq, wr = self._services[service]
    #         wid = wq.get()
    #         if not wid:
    #             # no worker ready
    #             # queue message
    #             msg.insert(0, service)
    #             wr.append((proto, rp, msg))
    #             return
    #         wrep = self._workers[wid]
    #         to_send = [wrep.id, b'', self.WORKER_PROTO, b'\x02']
    #         to_send.extend(rp)
    #         to_send.append(b'')
    #         to_send.extend(msg)
    #         self.main_stream.send_multipart(to_send)
    #     except KeyError:
    #         # unknwon service
    #         # ignore request
    #         print('broker has no service "%s"' % service)
    #     return
    #
    # def on_worker(self, proto, rp, msg):
    #     """Method called on worker message.
    #
    #     Frame 0 of msg is the command id.
    #     The remaining frames depend on the command.
    #
    #     This method determines the command sent by the worker and
    #     calls the appropriate method. If the command is unknown the
    #     message is ignored and a DISCONNECT is sent.
    #
    #     :param proto: the protocol id sent
    #     :type proto:  str
    #     :param rp:  return address stack
    #     :type rp:   list of str
    #     :param msg: message parts
    #     :type msg:  list of str
    #
    #     :rtype: None
    #     """
    #     cmd = msg.pop(0)
    #     if cmd in self._worker_cmds:
    #         fnc = self._worker_cmds[cmd]
    #         fnc(rp, msg)
    #     else:
    #         # ignore unknown command
    #         # DISCONNECT worker
    #         self.disconnect(rp[0])
    #     return
    #

# class WorkerRep(object):
#     """Helper class to represent a worker in the broker.
#
#     Instances of this class are used to track the state of the attached worker
#     and carry the timers for incomming and outgoing heartbeats.
#
#     :param proto:    the worker protocol id.
#     :type wid:       str
#     :param wid:      the worker id.
#     :type wid:       str
#     :param service:  service this worker serves
#     :type service:   str
#     :param stream:   the ZMQStream used to send messages
#     :type stream:    ZMQStream
#     """
#
#     def __init__(self, proto, wid, service, stream):
#         self.proto = proto
#         self.id = wid
#         self.service = service
#         self.curr_liveness = HB_LIVENESS
#         self.stream = stream
#         self.last_hb = 0
#         self.hb_out_timer = PeriodicCallback(self.send_hb, HB_INTERVAL)
#         self.hb_out_timer.start()
#         return
#
#     def send_hb(self):
#         """Called on every HB_INTERVAL.
#
#         Decrements the current liveness by one.
#
#         Sends heartbeat to worker.
#         """
#         self.curr_liveness -= 1
#         msg = [self.id, b'', self.proto, b'\x04']
#         self.stream.send_multipart(msg)
#         return
#
#     def on_heartbeat(self):
#         """Called when a heartbeat message from the worker was received.
#
#         Sets current liveness to HB_LIVENESS.
#         """
#         self.curr_liveness = HB_LIVENESS
#         return
#
#     def is_alive(self):
#         """Returns True when the worker is considered alive.
#         """
#         return self.curr_liveness > 0
#
#     def shutdown(self):
#         """Cleanup worker.
#
#         Stops timer.
#         """
#         self.hb_out_timer.stop()
#         self.hb_out_timer = None
#         self.stream = None
#         return


# class ServiceQueue(object):
#     """Class defining the Queue interface for workers for a service.
#
#     The methods on this class are the only ones used by the broker.
#     """
#
#     def __init__(self):
#         """Initialize queue instance.
#         """
#         self.q = []
#         return
#
#     def __contains__(self, wid):
#         """Check if given worker id is already in queue.
#
#         :param wid:    the workers id
#         :type wid:     str
#         :rtype:        bool
#         """
#         return wid in self.q
#
#     def __len__(self):
#         return len(self.q)
#
#     def remove(self, wid):
#         try:
#             self.q.remove(wid)
#         except ValueError:
#             pass
#         return
#
#     def put(self, wid, *args, **kwargs):
#         if wid not in self.q:
#             self.q.append(wid)
#         return
#
#     def get(self):
#         if not self.q:
#             return None
#         return self.q.pop(0)
