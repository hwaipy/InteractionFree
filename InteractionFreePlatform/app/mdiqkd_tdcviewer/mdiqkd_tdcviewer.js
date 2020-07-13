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
  // setFetchingProgress(0.0)

  worker = new IFWorker("ws://" + window.location.host + "/ws", function() {
    fetcher = new TDCStorageStreamFatcher(worker, collection, 500, {
      'Data.Counter': 1,
      'Data.MultiHistogram': 1
    }, plot, listener)
    fetcher.start()
  })
});

function plot(result, append) {
  var layout = {
    xaxis: {
      title: 'Time (ns)'
    },
    yaxis: {
      title: 'Count'
    },
  }
  if (result == null) {
    var traces = [{
      x: [0],
      y: [0],
      type: 'scatter',
      name: 'CH0'
    }]
    $('#HistogramWarning')[0].classList.add('d-none')
  } else {
    console.log(append);
    var data = result['Data']['MultiHistogram']
    var configuration = data['Configuration']
    var histograms = data['Histograms']
    var viewFrom = configuration['ViewStart'] / 1000.0;
    var viewTo = configuration['ViewStop'] / 1000.0;
    var divide = configuration['Divide'];
    var length = configuration['BinCount'];
    var syncChannel = configuration['Sync'];
    var signalChannels = configuration['Signals'];
    var xs = linspace(viewFrom, viewTo / divide, length)
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
    layout['uirevision'] = 'true'
  }
  Plotly.react('viewport', traces, layout, {
    displaylogo: false,
    // responsive: true
  })
}

function updateIntegralData() {
  var beginTime = onBlurIntegralRange('input-integral-from')
  var endTime = onBlurIntegralRange('input-integral-to')
  invalid = $("#input-integral-from")[0].classList.contains('is-invalid') ||
    $("#input-integral-to")[0].classList.contains('is-invalid')
  var isToNow = $("#input-integral-to")[0].value
  var isToNow = isToNow.length == 0 || isToNow.toLowerCase() == 'now'
  if (!invalid) fetcher.updateIntegralData(beginTime, endTime, isToNow)
}

function onSelectionIntegral(isIntegral) {
  $("#selection-instant").attr("class", isIntegral ? "btn btn-secondary" :
    "btn btn-success")
  $("#selection-integral").attr("class", isIntegral ? "btn btn-success" :
    "btn btn-secondary")
  $("#IntegralConfig").collapse(isIntegral ? "show" : "hide")
  fetcher.changeMode(isIntegral ? "Stop" : "Instant")
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

function listener(event, arg) {
  if (event == 'FetchTimeDelta') {
    fetchTimeDelta = arg
    if (fetchTimeDelta > 3000) {
      $('#HistogramWarning')[0].classList.remove('d-none')
      $('#HistogramWarningContent').html("The most recent data was fetched " + parseInt(fetchTimeDelta / 1000) + " s ago.")
    } else {
      $('#HistogramWarning')[0].classList.add('d-none')
    }
  } else if (event == 'FetchingProgress') {
    progress = parseInt(arg * 100)
    $('#FetchingProgress').attr('style', 'background-image: linear-gradient(to right, #BDE6FF ' + (progress) + '%, #F8F9FC ' + (progress) + '%)')
  } else if (event == 'FetchingNumber') {
    if (arg == null) {
      $('#FetchNumberContent').html('')
      $('#FetchNumber')[0].classList.add('d-none')
    } else {
      integralFetchedDataCount = arg[0]
      integralTotalDataCount = arg[1]
      integralTime = arg[2]
      content = integralTotalDataCount + ' items (in ' + integralTime + ' s)'
      if (integralFetchedDataCount < integralTotalDataCount) content = integralFetchedDataCount + ' / ' + content
      $('#FetchNumber')[0].classList.remove('d-none')
      $('#FetchNumberContent').html(content)
    }
  } else {
    console.log(event + ', '+ arg);
  }
}



































































// class TDCViewerStorageStreamFatcher {
//   constructor(worker, collection) {
//     this.worker = worker
//     this.collection = collection
//     this.lastTime = null
//       // modes: Instant, Integral, IntegralContinues
//     this.mode = 'Instant'
//     this.filter = {
//       'Data.Counter': 1,
//       'Data.MultiHistogram': 1
//     }
//     this.fetchID = 0
//     this.integralTime = 0
//     this.integralBeginTime = null
//     this.integralEndTime = null
//     this.integralMostRecentTime = null
//     this.integralFetchedDataCount = 0
//     this.integralTotalDataCount = 0
//     this.integralContinuesHasNew = false
//     this.clearPlot()
//   }
//
//   start(interval) {
//     this.update()
//     setInterval("viewerFetcher.update()", '' + interval)
//   }
//
//   update() {
//     if (this.mode == 'Instant' || this.mode == 'IntegralContinues') {
//       var fetchID = this.fetchID
//       worker.request("Storage", "latest", [this.collection, this.lastTime, this.filter], {},
//         function(result) {
//           if (fetchID == viewerFetcher.fetchID) {
//             if (result != null) {
//               viewerFetcher.lastTime = result['FetchTime'];
//               if (viewerFetcher.mode == 'Instant' || viewerFetcher.mode == 'IntegralContinues') {
//                 viewerFetcher.updateResult(result, fetchID, 'update')
//               }
//             }
//             if (viewerFetcher.mode == 'IntegralContinues') {
//               viewerFetcher.integralTime = parseInt((new Date().getTime() - viewerFetcher.integralBeginTime.getTime())/1000)
//               if (result != null){
//                 viewerFetcher.integralTotalDataCount += 1
//                 viewerFetcher.integralFetchedDataCount += 1
//               }
//             }
//             viewerFetcher.updateFetchingInfo()
//           }
//         },
//         function(error) {
//           console.log("Error: " + error)
//         }
//       )
//     }
//     viewerFetcher.updateFetchingInfo()
//   }
//
//   range(beginTime, endTime) {
//     var fetchID = this.fetchID
//     this.integralTime = parseInt((endTime.getTime() - beginTime.getTime())/1000)
//     worker.request("Storage", "range", [this.collection, dateToISO(beginTime), dateToISO(endTime), 'FetchTime', this.filter], {},
//       function(result) {
//         viewerFetcher.integralTotalDataCount += result.length
//         for (var i = 0; i < result.length; i++) {
//           worker.request("Storage", "get", [viewerFetcher.collection, result[i]['_id'], viewerFetcher.filter], {},
//             function(result) {
//               if (fetchID == viewerFetcher.fetchID) {
//                 viewerFetcher.updateResult(result)
//                 viewerFetcher.integralFetchedDataCount += 1
//                 viewerFetcher.updateFetchingInfo()
//               }
//             },
//             function(error) {
//               console.log("Error: " + error)
//             })
//           viewerFetcher.integralMostRecentTime = new Date();
//           viewerFetcher.integralMostRecentTime.setTime(Date.parse(result[i]['FetchTime']))
//           console.log(viewerFetcher.integralMostRecentTime);
//         }
//       },
//       function(error) {
//         console.log("Error: " + error)
//       }
//     )
//   }
//
//   updateResult(result) {
//     var data = result['Data']['MultiHistogram']
//     var configuration = data['Configuration']
//     var histograms = data['Histograms']
//     var viewFrom = configuration['ViewStart'] / 1000.0;
//     var viewTo = configuration['ViewStop'] / 1000.0;
//     var divide = configuration['Divide'];
//     var length = configuration['BinCount'];
//     var syncChannel = configuration['Sync'];
//     var signalChannels = configuration['Signals'];
//     var xs = linspace(viewFrom, viewTo / divide, length)
//     var traces = []
//     for (var i = 0; i < signalChannels.length; i++) {
//       var channelNum = signalChannels[i].toString()
//       if (channelNum.length == 1) channelNum = "0" + channelNum
//       traces.push({
//         x: xs,
//         y: histograms[i],
//         type: 'scatter',
//         name: 'CH' + channelNum
//       })
//     }
//     var layout = {
//       xaxis: {
//         title: 'Time (ns)'
//       },
//       yaxis: {
//         title: 'Count'
//       },
//       uirevision:'true',
//     };
//     Plotly.react('viewport', traces, layout, {
//       displaylogo: false,
//       // responsive: true
//     });
//   }
//
//   clearPlot() {
//     var traces = [{
//       x: [0],
//       y: [0],
//       type: 'scatter',
//       name: 'CH0'
//     }]
//     var layout = {
//       xaxis: {
//         title: 'Time (ns)'
//       },
//       yaxis: {
//         title: 'Count'
//       }
//     };
//     Plotly.react('viewport', traces, layout, {
//       displaylogo: false,
//       // responsive: true
//     });
//     $('#HistogramWarning')[0].classList.add('d-none')
//   }
//
//   updateFetchingInfo() {
//     // Check if display no data warning
//     var fetchTimeDelta = 0
//     if (this.mode == 'Instant') {
//       fetchTimeDelta = new Date().getTime() - Date.parse(this.lastTime)
//     } else if (this.mode == 'IntegralContinues') {
//       if (this.integralContinuesHasNew) {
//         fetchTimeDelta = new Date().getTime() - Date.parse(this.lastTime)
//       } else {
//         if (this.integralFetchedDataCount == this.integralTotalDataCount && this.integralMostRecentTime != null) {
//           fetchTimeDelta = new Date().getTime() - this.integralMostRecentTime.getTime()
//         }
//       }
//     }
//     if (this.mode == 'Integral' || this.mode == 'IntegralContinues') {
//       if (this.integralFetchedDataCount == 0) {
//         fetchTimeDelta = 0
//       }
//     }
//     if (fetchTimeDelta > 3000) {
//       $('#HistogramWarning')[0].classList.remove('d-none')
//       $('#HistogramWarningContent').html("The most recent data was fetched " + parseInt(fetchTimeDelta / 1000) + " s ago.")
//     } else {
//       $('#HistogramWarning')[0].classList.add('d-none')
//     }
//
//     // Set prograss
//     if (this.integralTotalDataCount > 0 && this.integralFetchedDataCount < this.integralTotalDataCount) {
//       setFetchingProgress(this.integralFetchedDataCount * 1.0 / this.integralTotalDataCount)
//     } else {
//       setFetchingProgress(0.0)
//     }
//
//     // Set FetchNumber
//     if (this.mode == 'Integral' || this.mode == 'IntegralContinues') {
//       var content = this.integralTotalDataCount + ' items (in ' + this.integralTime + ' s)'
//       if (this.integralFetchedDataCount < this.integralTotalDataCount) {
//         content = this.integralFetchedDataCount + '/' + content
//       }
//       $('#FetchNumber')[0].classList.remove('d-none')
//       $('#FetchNumberContent').html(content)
//     } else {
//       $('#FetchNumberContent').html('')
//       $('#FetchNumber')[0].classList.add('d-none')
//     }
//   }
//
//   changeMode(mode) {
//     if (mode != 'Instant' && mode != 'Integral' && mode !=
//       'IntegralContinues' && mode != 'Stop') {
//       console.log('Bad mode: ' + mode)
//       return
//     }
//     this.mode = mode
//     this.integralTime = 0
//     this.integralTotalDataCount = 0
//     this.integralFetchedDataCount = 0
//     this.integralContinuesHasNew = false
//     if (mode == 'Instant') this.lastTime = 0
//     if (mode != 'Stop') this.fetchID += 1
//     this.clearPlot()
//   }
// }
//
// function updateIntegralData() {
//   var beginTime = onBlurIntegralRange('input-integral-from')
//   var endTime = onBlurIntegralRange('input-integral-to')
//   invalid = $("#input-integral-from")[0].classList.contains('is-invalid') ||
//     $("#input-integral-to")[0].classList.contains('is-invalid')
//   var isToNow = $("#input-integral-to")[0].value
//   var isToNow = isToNow.length == 0 || isToNow.toLowerCase() == 'now'
//   if (!invalid) {
//     viewerFetcher.integralBeginTime = beginTime
//     viewerFetcher.integralEndTime = endTime
//     viewerFetcher.changeMode(isToNow ? "IntegralContinues" : "Integral")
//     if(isToNow) viewerFetcher.lastTime = dateToISO(endTime)
//     viewerFetcher.range(beginTime, endTime)
//   }
// }
//
// function onSelectionIntegral(isIntegral) {
//   $("#selection-instant").attr("class", isIntegral ? "btn btn-secondary" :
//     "btn btn-success")
//   $("#selection-integral").attr("class", isIntegral ? "btn btn-success" :
//     "btn btn-secondary")
//   $("#IntegralConfig").collapse(isIntegral ? "show" : "hide")
//   viewerFetcher.changeMode(isIntegral ? "Stop" : "Instant")
// }
//
// function onBlurIntegralRange(id) {
//   element = $("#" + id)[0]
//   text = element.value
//   isNow = false
//   if (text.length == 0 || text.toLowerCase() == "now") {
//     parsedDate = new Date()
//     isNow = (id == 'input-integral-to')
//   } else parsedDate = parseSimpleDate(text)
//   classList = element.classList
//   if (parsedDate) {
//     classList.remove('is-invalid')
//     if (!isNow) element.value = dateToString(parsedDate)
//   } else {
//     classList.add('is-invalid')
//   }
//   return parsedDate
// }
//
// function dateToISO(date) {
//   return dateToString(date).replace(' ', 'T') + '.000000+08:00'
// }
//
// function setFetchingProgress(p) {
//   progress = parseInt(p * 100)
//   $('#FetchingProgress').attr('style', 'background-image: linear-gradient(to right, #BDE6FF ' + (progress) + '%, #F8F9FC ' + (progress) + '%)')
// }
