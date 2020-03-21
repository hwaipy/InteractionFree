# InteractionFree

*v1.0.20200320*

------

InteractionFree is a remote procedure call (RPC) framework that is initially designed for device control and data processing in quantum optics lab. Nevertheless, is can be used in any scene of distributed computing.



### Topology

InteractionFree frame currently support star structure. There is a server (called Broker) that take TCP connections from all clients (called Worker). Thus, the IP address of the server should be reachable for all clients.



### Protocol

The framework is basically build on [ZeroMQ](https://zeromq.org/), thus remains a high flexibility of update in the future. A Broker is a ROUTER, while a Worker is a DEALER. When a Worker connects to the Broker, an identical address is assigned to the connection. Workers communicate to each other and to the Broker by sending Messages. A Message is a standard ZeroMQ multi-part message that organized as follows:


| &nbsp;Frame | &nbsp;Value | Explain |
| :-: | :-: | :-: |
| 0 | empty | Defined in ZeroMQ |
| 1 | 'IF1' | The version of InteractionFree |
|       2       | distributing-mode |         The distributing mode of the Message          |
|       3       |      address      |  The target that the Message is expected to send to   |
|       4       |      string       | The method of serialization for the following content |
| 5 to $\infin$ | | Depends on the method of serialization |

Frame 0 to 3 are all information that the Broker needs to know. Frame 4 to $\infin$ are normally meaningless bytes for the Broker and will be transported to the expected target intactly. When transporting large amount of data, Zero-Copy could be employed for better performance.

The target of a message is specified by Frame 2 and 3. InteractionFree version 1.0 now support the following mode:

| Distributing-Mode | Code |                           Address                            |
| :---------------: | :--: | :----------------------------------------------------------: |
|      Broker       | 0x00 | The Message is sending to the Broker, the address is undefined. Better to be empty. |
|      Direct       | 0x01 | The Message is sending to the Worker that has the corresponding address |
|      Service      | 0x02 |                 Explained in Service section                 |









# Problems to be solved

1. what if the address is used up for connections.