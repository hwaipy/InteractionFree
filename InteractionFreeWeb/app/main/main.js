$(document).ready(function() {
  worker = new IFWorker("ws://" + window.location.host + "/ws", function() {
    ping()
    setInterval("ping()", "2000")
  })
});

function ping(){
  t1 = new Date().getTime();
  worker.request("", "protocol", [], {}, function(result) {
    if(result == "IF1"){
      deltaT = new Date().getTime() - t1
      if(deltaT <= 30) setServerStatus(3)
      else if(deltaT <= 120) setServerStatus(2)
      else setServerStatus(1)
    } else {
      console.log("error (bad response): " + result)
      setServerStatus(0)
    }
    }, function(error) {
    console.log("error: " + error)
    setServerStatus(0)
  })
}

function setServerStatus(level){
  if(level == 3){
    $("#serverstatus").attr("class", "w3-text-green")
    $("#serverstatus").html("●●●")
  }
  if(level == 2){
    $("#serverstatus").attr("class", "w3-text-yellow")
    $("#serverstatus").html("●●")
  }
  if(level == 1){
    $("#serverstatus").attr("class", "w3-text-red")
    $("#serverstatus").html("●")
  }
  if(level == 0){
    $("#serverstatus").attr("class", "w3-text-gray")
    $("#serverstatus").html("Unkonwn")
  }
}
//<font color="green" class="w3-hide">●</font>
