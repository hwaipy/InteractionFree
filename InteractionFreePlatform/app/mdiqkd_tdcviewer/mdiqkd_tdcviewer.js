$(document).ready(function() {
  var parameterString = window.location.search
  var parameters = {}
  if (parameterString.length > 0) {
    parameterStrings = parameterString.split('?')[1].split('&')
    for (var i = 0; i < parameterStrings.length; i++) {
      paras = parameterStrings[i].split('=')
      if (paras.length == 2) parameters[paras[0]] = paras[1]
    }
  }
  collection = parameters['collection'] || "TDCLocalTest"

  worker = new IFWorker("ws://" + window.location.host + "/ws", function() {
    viewerFetcher = new TDCViewerStorageStreamFatcher(worker,
      collection)
    viewerFetcher.start(500)
  })
});

class TDCViewerStorageStreamFatcher {
  constructor(worker, collection) {
    this.worker = worker
    this.collection = collection
    this.lastTime = null
      // modes: Instant, Integral, IntegralContinues
    this.mode = 'Instant'
    this.filter = {
      'Data.Counter': 1,
      'Data.MultiHistogram': 1
    }
    this.fetchID = 0
    this.clearPlot()
  }

  start(interval) {
    // this.update()
    setInterval("viewerFetcher.update()", '' + interval)
  }

  update() {
    if (this.mode == 'Instant' || this.mode == 'IntegralContinues') {
      var fetchID = this.fetchID
      worker.request("Storage", "latest", [this.collection, this.lastTime,
          this.filter
        ], {},
        function(result) {
          if (result != null) {
            viewerFetcher.lastTime = result['FetchTime'];
            if (viewerFetcher.mode == 'Instant' ||
              viewerFetcher.mode == 'IntegralContinues') {
              viewerFetcher.updateResult(result, fetchID)
            }
          }
        },
        function(error) {
          console.log("Error: " + error)
        }
      )
    }
  }

  range(beginTime, endTime) {
    var fetchID = this.fetchID
    worker.request("Storage", "range", [this.collection, beginTime, endTime,
        'FetchTime', this.filter
      ], {},
      function(result) {
        for (var i = 0; i < result.length; i++) {
          worker.request("Storage", "get", [viewerFetcher.collection,
              result[i]['_id'], viewerFetcher.filter
            ], {},
            function(result) {
              viewerFetcher.updateResult(result, fetchID)
                // viewerFetcher.entryNum -= 1;
                // var chData = result['Data']['CoincidenceHistogram']
                // var chXs = chData['Configuration']
                // var chYs = chData['Histogram']
                // var meData = result['Data']['MDIQKDEncoding']
                // viewerFetcher.coincidenceHistogram.append(chXs, chYs)
                // var meConfigKeys = Object.keys(viewerFetcher.mdiqkdEncodingConfig)
                // for (var i = 0; i < meConfigKeys.length; i++) {
                //   var key = meConfigKeys[i];
                //   var hisIs = viewerFetcher.mdiqkdEncodingConfig[key]
                //   for (var j = 0; j < hisIs.length; j++) {
                //     var hisKey = viewerFetcher.histogramKeys[hisIs[j]]
                //     var his = meData[hisKey]
                //     viewerFetcher.mdiqkdEncodingHistograms[i].append(
                //       meData['Configuration'], his)
                //   }
                // }
                // if (viewerFetcher.entryNum == 0) {
                //   viewerFetcher.plot()
                // }
            },
            function(error) {
              console.log("Error: " + error)
            })
        }
      },
      function(error) {
        console.log("Error: " + error)
      }
    )
  }

  updateResult(result, fetchID) {
    if (fetchID == viewerFetcher.fetchID) {
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
        displaylogo: false,
        // responsive: true
      });
    }
    $('#HistogramWarning')[0].classList.add('d-none')
    var fetchTimeDelta = new Date().getTime() - Date.parse(result['FetchTime'])
    if (fetchTimeDelta > 3) {
      $('#HistogramWarning')[0].classList.remove('d-none')
      $('#HistogramWarningContent').html(
        "The most recent data was fetched " + parseInt(fetchTimeDelta /
          1000) + " s ago.")
    }
  }

  clearPlot() {
    var traces = [{
      x: [0],
      y: [0],
      type: 'scatter',
      name: 'CH0'
    }]
    var layout = {
      xaxis: {
        title: 'Time (ns)'
      },
      yaxis: {
        title: 'Count'
      }
    };
    Plotly.react('viewport', traces, layout, {
      displaylogo: false,
      // responsive: true
    });
    $('#HistogramWarning')[0].classList.add('d-none')
  }

  changeMode(mode) {
    if (mode != 'Instant' && mode != 'Integral' && mode !=
      'IntegralContinues' && mode != 'Stop') {
      console.log('Bad mode: ' + mode)
      return
    }
    this.mode = mode
    if (mode == 'Instant') this.lastTime = 0
    if (mode != 'Stop') this.fetchID += 1
    this.clearPlot()
  }
}

function updateIntegralData() {
  var beginTime = onBlurIntegralRange('input-integral-from')
  var endTime = onBlurIntegralRange('input-integral-to')
  invalid = $("#input-integral-from")[0].classList.contains('is-invalid') ||
    $("#input-integral-to")[0].classList.contains('is-invalid')
  var isToNow = $("#input-integral-to")[0].value
  var isToNow = isToNow.length == 0 || isToNow.toLowerCase() == 'now'
  if (!invalid) {
    viewerFetcher.changeMode(isToNow ? "IntegralContinues" : "Integral")
    viewerFetcher.range(dateToString(beginTime) + '.000000',
      dateToString(endTime) + '.000000')
  }
}

function onSelectionIntegral(isIntegral) {
  $("#selection-instant").attr("class", isIntegral ? "btn btn-secondary" :
    "btn btn-success")
  $("#selection-integral").attr("class", isIntegral ? "btn btn-success" :
    "btn btn-secondary")
  $("#IntegralConfig").collapse(isIntegral ? "show" : "hide")
  viewerFetcher.changeMode(isIntegral ? "Stop" : "Instant")
}

function onBlurIntegralRange(id) {
  element = $("#" + id)[0]
  text = element.value
  isNow = false
  if (text.length == 0 || text.toLowerCase() == "now") {
    parsedDate = new Date()
    isNow = (id == 'input-integral-to')
  } else parsedDate = parseSimpleDate(text)
  classList = element.classList
  if (parsedDate) {
    classList.remove('is-invalid')
    if (!isNow) element.value = dateToString(parsedDate)
  } else {
    classList.add('is-invalid')
  }
  return parsedDate
}
