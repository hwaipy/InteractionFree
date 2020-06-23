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

  worker = new IFWorker("ws://" + window.location.host + "/ws", function() {
    viewerFetcher = new TDCViewerStorageStreamFatcher(worker,
      "TDCLocalTest_10k250M")
    viewerFetcher.start(1000)
  })
});

class TDCViewerStorageStreamFatcher {
  constructor(worker, collection) {
    this.worker = worker
    this.collection = collection
    this.entryNum = -1
    this.coincidenceHistogram = new Histogram()
    this.histogramKeys = {
      0: 'Histogram with RandomNumber[0]',
      1: 'Histogram with RandomNumber[1]',
      2: 'Histogram with RandomNumber[2]',
      3: 'Histogram with RandomNumber[3]',
      4: 'Histogram with RandomNumber[4]',
      5: 'Histogram with RandomNumber[5]',
      6: 'Histogram with RandomNumber[6]',
      7: 'Histogram with RandomNumber[7]',
      10: 'Histogram Alice Time',
      11: 'Histogram Bob Time',
    }
    this.mdiqkdEncodingConfig = {
      'All Pulses': [0, 1, 2, 3, 4, 5, 6, 7],
      'Vacuum': [0, 1],
      'Z 0': [6],
      'Z 1': [7],
      'X': [2, 3],
      'Y': [4, 5],
      'Alice Delay': [10],
      'Bob Delay': [11],
    }
    this.mdiqkdEncodingHistograms = new Array(Object.keys(this.mdiqkdEncodingConfig)
      .length)
    for (var i = 0; i < Object.keys(this.mdiqkdEncodingConfig).length; i++) {
      this.mdiqkdEncodingHistograms[i] = new Histogram()
    }
  }

  start(interval) {
    this.fetch()
      // setInterval("viewerFetcher.update()", "1000")
  }

  fetch() {
    console.log('fetching');
    worker.request("Storage", "range", [this.collection,
        "2020-04-05 22:22:00.000000", "2020-05-05 22:35:00.000000",
        'FetchTime'
      ], {},
      function(result) {
        viewerFetcher.entryNum = result.length
        for (var i = 0; i < result.length; i++) {
          viewerFetcher.getOne(result[i]['_id'])
        }
      },
      function(error) {
        console.log("error: " + error)
      })
  }

  getOne(id) {
    worker.request("Storage", "get", [this.collection, id, {
        'Data.Counter': 1,
        'Data.CoincidenceHistogram': 1,
        'Data.MDIQKDEncoding': 1,
      }], {},
      function(result) {
        viewerFetcher.entryNum -= 1;
        var chData = result['Data']['CoincidenceHistogram']
        var chXs = chData['Configuration']
        var chYs = chData['Histogram']
        var meData = result['Data']['MDIQKDEncoding']
        viewerFetcher.coincidenceHistogram.append(chXs, chYs)
        var meConfigKeys = Object.keys(viewerFetcher.mdiqkdEncodingConfig)
        for (var i = 0; i < meConfigKeys.length; i++) {
          var key = meConfigKeys[i];
          var hisIs = viewerFetcher.mdiqkdEncodingConfig[key]
          for (var j = 0; j < hisIs.length; j++) {
            var hisKey = viewerFetcher.histogramKeys[hisIs[j]]
            var his = meData[hisKey]
            viewerFetcher.mdiqkdEncodingHistograms[i].append(
              meData['Configuration'], his)
          }
        }

        // console.log(0);
        // console.log(viewerFetcher.mdiqkdEncodingHistograms[0].ys);
        // console.log(2);
        // console.log(viewerFetcher.mdiqkdEncodingHistograms[2].ys);

        if (viewerFetcher.entryNum == 0) {
          viewerFetcher.plot()
        }
      },
      function(error) {
        console.log("error: " + error)
      })
  }

  plot() {
    viewerFetcher.doPlot('coincidenceChart', viewerFetcher.coincidenceHistogram,
      function(xs) {
        return new Array(xs['ViewStart'] / 1000.0, xs['ViewStop'] / 1000.0)
      })
    var meCharts = ['meAllPulses', 'meVacuum', 'meZ0', 'meZ1', 'meX', 'meY',
      'meAliceTime', 'meBobTime'
    ]
    for (var i = 0; i < meCharts.length; i++) {
      viewerFetcher.doPlot(meCharts[i], viewerFetcher.mdiqkdEncodingHistograms[
        i], function(xs) {
        return new Array(0, xs['Period'] / 1000.0)
      })
    }
    // console.log(viewerFetcher.mdiqkdEncodingHistograms[0].xs);
    // console.log(viewerFetcher.mdiqkdEncodingHistograms[0].ys);
    // var viewFrom = histogram.xs[] / 1000.0;
    // var viewTo = histogram.xs['ViewStop'] / 1000.0;
  }

  doPlot(divID, histogram, xsRange) {
    var xs = histogram.xs
    if (xsRange) {
      var range = xsRange(histogram.xs)
      var viewFrom = range[0];
      var viewTo = range[1];
      var length = histogram.ys.length;
      xs = histogram.genXs(viewFrom, viewTo, length)
    }
    var traces = [{
      x: xs,
      y: histogram.ys,
      type: 'scatter'
    }]
    var layout = {
      xaxis: {
        title: 'Time (ns)'
      },
      yaxis: {
        title: 'Count'
      }
    };
    Plotly.react(divID, traces, layout, {
      displaylogo: false
    });
  }

  checkConfAndHist(chData, chConfiguration, meData, meConfiguration) {
    if (viewerFetcher.chConfiguration == null) {
      viewerFetcher.chConfiguration = chConfiguration
      viewerFetcher.meConfiguration = meConfiguration
      viewerFetcher.chHistogram = new Array(chConfiguration['BinCount'])
      viewerFetcher.meHistogram = new Array(meConfiguration['BinCount'])
      for (var i = 0; i < viewerFetcher.chHistogram.length; i++) {
        viewerFetcher.chHistogram[i] = 0
      }
      for (var i = 0; i < viewerFetcher.meHistogram.length; i++) {
        viewerFetcher.meHistogram[i] = 0
      }
    } else {
      if (!_.isEqual(viewerFetcher.chConfiguration, chConfiguration)) {
        viewerFetcher.configurationMatch = false
      }
      if (!_.isEqual(viewerFetcher.meConfiguration, meConfiguration)) {
        viewerFetcher.configurationMatch = false
      }
    }
  }
}
