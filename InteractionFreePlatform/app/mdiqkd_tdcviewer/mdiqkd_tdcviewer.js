$(document).ready(function() {
  var parameterString = window.location.search
  var parameters = {}
  if (parameterString.length > 0){
    parameterStrings = parameterString.split('?')[1].split('&')
    for(var i=0;i<parameterStrings.length;i++){
      paras = parameterStrings[i].split('=')
      if (paras.length == 2) parameters[paras[0]] = paras[1]
    }
  }
  collection = parameters['collection'] || "TDCLocalTest"

  // worker = new IFWorker("ws://" + window.location.host + "/ws", function() {
  //   viewerFetcher = new TDCViewerStorageStreamFatcher(worker, collection)
  //   viewerFetcher.start(1000)
  // })

  parseSimpleDate('11:02:59A')
  // parseSimpleDate('23:1')
  parseSimpleDate('11:22:59')
  // parseSimpleDate('1 11:02:59')
  // parseSimpleDate('201-1-1 11:02:59')
});

class TDCViewerStorageStreamFatcher {
  constructor(worker, collection) {
    this.worker = worker
    this.collection = collection
    this.lastTime = null
  }

  start(interval) {
    this.update()
    setInterval("viewerFetcher.update()", "1000")
  }

  update() {
    worker.request("Storage", "latest", [this.collection, this.lastTime, {
        'Data.Counter': 1,
        'Data.MultiHistogram': 1
      }], {},
      function(result) {
        if (result != null) {
          viewerFetcher.lastTime = result['RecordTime'];
          var data = result['Data']['MultiHistogram']
          var configuration = data['Configuration']
          var histograms = data['Histograms']
          var viewFrom = configuration['ViewStart'] / 1000.0;
          var viewTo = configuration['ViewStop'] / 1000.0;
          var divide = configuration['Divide'];
          var length = configuration['BinCount'];
          var syncChannel = configuration['Sync'];
          var signalChannels = configuration['Signals'];
          var xs = linspace(viewFrom, viewTo / divide,
            length)
          var traces = []
          for (var i = 0; i < signalChannels.length; i++) {
            var channelNum = signalChannels[i].toString()
            if (channelNum.length == 1) channelNum = "0" + channelNum
            traces.push({
              x: xs,
              y: histograms[i],
              type: 'scatter',
              name: 'CH' + channelNum
            })
          }
          var layout = {
            xaxis: {
              title: 'Time (ns)'
            },
            yaxis: {
              title: 'Count'
            }
          };
          Plotly.react('viewport', traces, layout, {
            displaylogo: false
          });
        }
      },
      function(error) {
        console.log("error: " + error)
      })
  }
}

function onSelectionIntegral(isIntegral){
  $("#selection-instant").attr("class", isIntegral ? "btn btn-secondary" : "btn btn-success")
  $("#selection-integral").attr("class", isIntegral ? "btn btn-success" : "btn btn-secondary")
  $("#IntegralConfig").collapse(isIntegral ? "show" : "hide")
}

function onInputIntegralRange(event, id){
  // v = $("#"+id)[0].value
  // d = new Date()
  // d.setTime(Date.parse(v))
  // console.log(d);
}

function onBlurIntegralRange(event, id){
  v = $("#"+id)[0].value
  parsedDate = parseSimpleDate(v)
  console.log(parsedDate);
}
