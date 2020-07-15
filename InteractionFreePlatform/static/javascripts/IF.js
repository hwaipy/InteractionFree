class IFWorkerCore {
  constructor(endpoint) {
    this.messageIDs = 0
    this.endpoint = endpoint
    this.dealer = new JSMQ.Dealer()
    this.connected = false
    this.dealer.onMessage = (this._onMessage).bind(this)
    this.waitingList = new Map()
    this.timeout = 3000
  }

  async connect() {
    if (this.connected) return
    var __this = this
    return new Promise(function(resolve, reject) {
      __this.dealer.sendReady = function () {
        __this.connected = true
        resolve('OK')
      }
      __this.dealer.connect(__this.endpoint)
    })
  }

  async request(target, functionName, args, kwargs) {
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
    if (target == "") {
      message.addString("Broker")
      message.addString("")
    } else {
      message.addString("Service")
      message.addString(target)
    }
    message.addString("Msgpack")
    message.addBuffer(contentBuffer)
    var __this = this
    var promise = new Promise(function(resolve, reject){
      __this.waitingList.set(messageID, [resolve, reject])
    })
    this.dealer.send(message)
    setTimeout(()=>{
      this._onResponse({
        'ResponseID': messageID,
        'Error': 'Timeout',
      })
    }, this.timeout)
    return promise
  }

  _onResponse(content) {
    var responseID = content["ResponseID"];
    var result = content["Result"]
    var error = content["Error"]
    if (this.waitingList.has(responseID)) {
      var promise = this.waitingList.get(responseID)
      this.waitingList.delete(responseID)
      if (error) {
        promise[1](error)
      } else {
        promise[0](result)
      }
    }
  }

  _onRequest(content) {
    console.log("onRequest not implemented.");
  }

  _onMessage(message) {
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
          this._onResponse(content)
        } else if (messageType == "Request") {
          this._onRequest(content)
        } else {
          console.log("Bad message type: " + messageType + ".");
        }
      }
    } else {
      console.log("Invalid message that contains " + message.getSize() + " frames.");
    }
  }

  _createProxy(path) {
    var __this = this
    function remoteFunction() {
    }
    return new Proxy(remoteFunction, {
      get: function (target, key, receiver) {
        if (key == 'then' && path == '') return undefined
        return __this._createProxy(path + '.' + key)
      },
      apply: function (target, thisArg, args) {
        var items = path.split('.')
        if (items.length != 2 && items.length != 3) {
          throw new Error('[' + path + '] is not a valid remote function.');
        }
        return __this.request(items[items.length - 2], items[items.length - 1], args, {})
      },
    })
  }
}

async function IFWorker(endpoint) {
  var core = new IFWorkerCore(endpoint)
  await core.connect()
  return core._createProxy('')
}
