# InteractionFree

*v0.1.20200320*

------

InteractionFree is a remote procedure call (RPC) framework that is initially designed for device control and data processing in quantum optics lab. Nevertheless, is can be used in any scene of distributed computing.



### Topology

##### Transport Layer

InteractionFree frame currently support star structure. There is a server (called Broker) that take TCP connections from all clients (called Worker). Thus, the IP address of the server should be reachable for all clients.



### Protocol

##### Transport Layer

The framework is basically build on [ZeroMQ](https://zeromq.org/), thus remains a high flexibility of update in the future. Workers communicate to each other and to the Broker by sending Messages. An InteractionFree