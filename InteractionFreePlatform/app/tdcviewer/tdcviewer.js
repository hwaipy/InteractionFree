$(document).ready(function() {
  worker = new IFWorker("ws://" + window.location.host + "/ws", function() {
    viewerFetcher = new TDCViewerStorageStreamFatcher(worker,
      "TDCLocalTest_10k100M_100")
    viewerFetcher.start(1000)
  })
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

function linspace(a, b, n) {
  if (typeof n === "undefined") n = Math.max(Math.round(b - a) + 1, 1);
  if (n < 2) {
    return n === 1 ? [a] : [];
  }
  var i, ret = Array(n);
  n--;
  for (i = n; i >= 0; i--) {
    ret[i] = (i * b + (n - i) * a) / n;
  }
  return ret;
}
