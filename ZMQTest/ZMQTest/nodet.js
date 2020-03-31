// console.log("1");
// const zmq = require('jszmq');
// console.log("2");
// const dealer = zmq.socket('pub');
// console.log("3");
// dealer.bind('ws://127.0.0.1:8887');
// console.log("4");
// dealer.send('Hello'); // Single frame
// console.log("5");


const http = require('http');
const zmq = require('jszmq');

const server = http.createServer();

const rep = new zmq.Rep();
const pub = new zmq.Pub();

rep.bind('ws://localhost:80/reqrep', server);
pub.bind('ws://localhost:80/pubsub', server);

server.listen(80);
