$(document).ready(async function() {
  var endpoint = 'ws://' + window.location.host + '/ws'
  var parameterString = window.location.search
  var parameters = {}
  if (parameterString.length > 0) {
    parameterStrings = parameterString.split('?')[1].split('&')
    for (var i = 0; i < parameterStrings.length; i++) {
      paras = parameterStrings[i].split('=')
      if (paras.length == 2) parameters[paras[0]] = paras[1]
    }
  }
  collection = parameters['collection'] || null

  worker = await IFWorker(endpoint)

  fetcher = new TDCStorageStreamFetcher(worker, collection, 500, {
    'Data.Counter': 1,
    // 'Data.CoincidenceHistogram': 1,
    // 'Data.MDIQKDEncoding.Configuration': 1,
    'Data.MDIQKDEncoding.Histogram with RandomNumber[0]': 1,
    'Data.MDIQKDEncoding.Histogram with RandomNumber[1]': 1,
    'Data.MDIQKDEncoding.Histogram with RandomNumber[2]': 1,
    'Data.MDIQKDEncoding.Histogram with RandomNumber[3]': 1,
    'Data.MDIQKDEncoding.Histogram with RandomNumber[4]': 1,
    'Data.MDIQKDEncoding.Histogram with RandomNumber[5]': 1,
    'Data.MDIQKDEncoding.Histogram with RandomNumber[6]': 1,
    'Data.MDIQKDEncoding.Histogram with RandomNumber[7]': 1,
    'Data.MDIQKDEncoding.Histogram Alice Time': 1,
    'Data.MDIQKDEncoding.Histogram Bob Time': 1,
  }, plot, listener)
  fetcher.start()
})

MEConfigs = [
  ['All Pulses', 'meAllPulses', [0, 1, 2, 3, 4, 5, 6, 7]],
  ['Vacuum', 'meVacuum', [0, 1]],
  ['Z 0', 'meZ0', [6]],
  ['Z 1', 'meZ1', [7]],
  ['X', 'meX', [2, 3]],
  ['Y', 'meY', [4, 5]],
  ['Alice Delay', 'meAliceTime', [10]],
  ['Bob Delay', 'meBobTime', [11]]
]

MEHistograms = new Array(MEConfigs.length)
for (var i = 0; i < MEHistograms.length; i++) {
  MEHistograms[i] = new Histogram()
}
for (var i = 0; i < MEConfigs.length; i++) {
  newItem = $('.MEViewPane').clone(true)
  newItem.removeClass('d-none')
  newItem.removeClass('MEViewPane')
  newItem.attr('id', 'MEViewPane_' + MEConfigs[i][1])
  $('.MEViewRow').append(newItem)
  newItem.find('.MEViewPort').attr('id', MEConfigs[i][1])
}

function plot(result, append) {
  var layout = {
    xaxis: {
      title: 'Time (ns)'
    },
    yaxis: {
      title: 'Count'
    },
  }
  var traces = []
  if (result == null) {
    for (var i = 0; i < MEHistograms.length; i++) {
      MEHistograms[i].clear()
      traces.push({
        x: [0],
        y: [0],
        type: 'scatter',
        name: ''
      })
    }
    $('#HistogramWarning')[0].classList.add('d-none')
  } else {


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
//     var histogramXsMatched = true
//     for (var i = 0; i < signalChannels.length; i++) {
//       var channelNum = signalChannels[i]
//       histogram = TDCHistograms[channelNum]
//       if (append) histogram.append(xs, histograms[i])
//       else histogram.update(xs, histograms[i])
//       var channelNumStr = signalChannels[i].toString()
//       if (channelNumStr.length == 1) channelNumStr = "0" + channelNumStr
//       traces.push({
//         x: histogram.xs,
//         y: histogram.ys,
//         type: 'scatter',
//         name: 'CH' + channelNumStr
//       })
//       histogramXsMatched &= histogram.xsMatch
//     }
//     layout['uirevision'] = 'true'
//     listener('HistogramXsMatched', histogramXsMatched)
  }
  for (var i = 0; i < MEConfigs.length; i++) {
    var config = MEConfigs[i]
    Plotly.react(config[1], traces[1], layout, {
      displaylogo: false,
      // responsive: true
    })
    console.log(config[1]);
    // Plotly.redraw(config[1])
  }
}

// function updateIntegralData() {
//   var beginTime = onBlurIntegralRange('input-integral-from')
//   var endTime = onBlurIntegralRange('input-integral-to')
//   invalid = $("#input-integral-from")[0].classList.contains('is-invalid') ||
//     $("#input-integral-to")[0].classList.contains('is-invalid')
//   var isToNow = $("#input-integral-to")[0].value
//   var isToNow = isToNow.length == 0 || isToNow.toLowerCase() == 'now'
//   if (!invalid) fetcher.updateIntegralData(beginTime, endTime, isToNow)
// }
//
// function onSelectionIntegral(isIntegral) {
//   $("#selection-instant").attr("class", isIntegral ? "btn btn-secondary" : "btn btn-success")
//   $("#selection-integral").attr("class", isIntegral ? "btn btn-success" : "btn btn-secondary")
//   $("#IntegralConfig").collapse(isIntegral ? "show" : "hide")
//   fetcher.changeMode(isIntegral ? "Stop" : "Instant")
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
  } else if (event == 'HistogramXsMatched') {
    if (!arg) {
      $('#HistogramError')[0].classList.remove('d-none')
      $('#HistogramErrorContent').html("Histogram Config Not Matched.")
    } else {
      $('#HistogramError')[0].classList.add('d-none')
    }
  } else if (event == 'TooManyRecords') {
    if (arg) {
      $('#TooManyRecordsError')[0].classList.remove('d-none')
      $('#TooManyRecordsErrorContent').html("Too Many Records.")
    } else {
      $('#TooManyRecordsError')[0].classList.add('d-none')
    }
  } else {
    console.log(event + ', '+ arg);
  }
}
