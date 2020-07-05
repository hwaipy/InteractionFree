$(document).ready(function() {
  worker = new IFWorker("ws://" + window.location.host + "/ws", function() {
    ping()
    setInterval("ping()", "2000")
  })
});

function ping() {
  t1 = new Date().getTime();
  worker.request("", "protocol", [], {}, function(result) {
    if (result == "IF1") {
      deltaT = new Date().getTime() - t1
      if (deltaT <= 30) setServerStatus(3, deltaT)
      else if (deltaT <= 120) setServerStatus(2, deltaT)
      else setServerStatus(1, deltaT)
    } else {
      console.log("error (bad response): " + result)
      setServerStatus(0)
    }
  }, function(error) {
    console.log("error: " + error)
    setServerStatus(0)
  })
}

function setServerStatus(level, delay) {
  if (level == 3) {
    $("#serverdelay").attr("class", "badge badge-success")
    $("#serverdelay").html(delay + ' ms')
  }
  if (level == 2) {
    $("#serverdelay").attr("class", "badge badge-warning")
    $("#serverdelay").html(delay + ' ms')
  }
  if (level == 1) {
    $("#serverdelay").attr("class", "badge badge-danger")
    $("#serverdelay").html(delay + ' ms')
  }
  if (level == 0) {
    $("#serverdelay").attr("class", "text-secondary")
    $("#serverdelay").html("Unkonwn")
  }
}
