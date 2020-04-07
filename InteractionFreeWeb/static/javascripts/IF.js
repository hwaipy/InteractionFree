class IFWorker {
  constructor(endpoint, onReady) {
    this.messageIDs = 0
    this.dealer = new JSMQ.Dealer()
    this.dealer.connect(endpoint)
    this.dealer.sendReady = onReady
    this.dealer.onMessage = (this.onMessage).bind(this)
    this.waitingList = new Map()
  }

  request(target, functionName, args, kwargs, onResponse, onError) {
    var content = {
      Type: "Request",
      Function: functionName,
      Arguments: args,
      KeyworkArguments: kwargs
    }
    var contentBuffer = msgpack.encode(content)
    var messageID = "" + (this.messageIDs++);
    var messageIDBuffer = new Uint8Array(messageID.length);
    StringUtility.StringToUint8Array(messageID, messageIDBuffer);
    var message = new JSMQ.Message();
    message.addString("")
    message.addString("IF1")
    message.addString(messageID)
    message.addString("Broker")
    message.addString("Msgpack")
    message.addBuffer(contentBuffer)
    this.waitingList.set(messageID, [onResponse, onError])
    this.dealer.send(message)
  }

  onResponse(content) {
    var responseIDBuffer = content["ResponseID"]
    var responseID = StringUtility.Uint8ArrayToString(responseIDBuffer);
    var result = content["Result"]
    var error = content["Error"]
    if (this.waitingList.has(responseID)) {
      var callbacks = this.waitingList.get(responseID)
      this.waitingList.delete(responseID)
      if (error) {
        callbacks[1](error)
      } else {
        callbacks[0](result)
      }
    }
  }

  onRequest(content) {
    console.log("onRequest not implemented.");
  }

  onMessage(message) {
    if (message.getSize() == 6) {
      var frame1empty = message.popBuffer()
      var frame2Protocol = message.popString()
      var frame3ID = message.popBuffer()
      var frame4From = message.popBuffer()
      var frame5Ser = message.popString()
      var frame6Content = message.popBuffer()
      if (frame2Protocol != "IF1") {
        console.log("Invalid Protocol: " + frame2Protocol + ".");
      } else if (frame5Ser != "Msgpack") {
        console.log("Invalid serialization: " + frame5Ser + ".");
      } else {
        var content = msgpack.decode(frame6Content)
        var messageType = content["Type"]
        if (messageType == "Response") {
          this.onResponse(content)
        } else if (messageType == "Request") {
          this.onRequest(content)
        } else {
          console.log("Bad message type: " + messageType + ".");
        }
      }
    } else {
      console.log("Invalid message that contains " + message.getSize() +
        " frames.");
    }
  }
}
