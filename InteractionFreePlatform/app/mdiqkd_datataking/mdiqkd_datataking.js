$(document).ready(async function() {
  initDeviceStatusPanel()
  var endpoint = 'ws://' + window.location.host + '/ws'

  worker = await IFWorker(endpoint)

  //   fetcher = new TDCStorageStreamFetcher(worker, collection, 500, filter,
  //     plot, listener)
  //   fetcher.start()
  setTimeout(updateDeviceStatusLoop)
})

worker = null

async function updateDeviceStatusLoop() {
  while (true) {
    try {
      var a = await worker.MDIQKD_GroundTDC.getPostProcessStatus()
    } catch (err) {
      console.log(err);
    }
    await sleep(800)
  }
}

function onDeviceStatusCheck(id) {
  var status = $('#' + id)[0].checked
}

// fillTrace = []
// for (var i = 0; i < markPoints.length; i++) {
//   markPoint = markPoints[i]
//   fillTrace.push({
//     x: [markPoint[0], markPoint[0], markPoint[1], markPoint[1]],
//     y: [-1e10, 1e10, 1e10, -1e10],
//     fill: 'toself',
//     type: 'scatter',
//     mode: 'none',
//     hoverinfo: 'none',
//     fillcolor: markPoint[2],
//   })
// }
//
// MEHistograms = new Array(MEConfigs.length)
// for (var i = 0; i < MEHistograms.length; i++) {
//   MEHistograms[i] = new Histogram()
// }
// for (var i = 0; i < MEConfigs.length; i++) {
//   newItem = $('.MEViewPane').clone(true)
//   newItem.removeClass('d-none')
//   newItem.removeClass('MEViewPane')
//   newItem.attr('id', 'MEViewPane_' + MEConfigs[i][1])
//   $('.MEViewRow').append(newItem)
//   newItem.find('.MEViewPort').attr('id', MEConfigs[i][1])
// }
// $('.MEViewPane').remove()
//
// function plot(result, append) {
//   var layout = {
//     xaxis: {
//       title: 'Time (ns)'
//     },
//     yaxis: {
//       title: 'Count'
//     },
//     margin: {
//       l: 50,
//       r: 30,
//       b: 50,
//       t: 30,
//       pad: 4
//     },
//     // width: 300,
//     height: 250,
//     showlegend: false,
//   }
//   var traces = []
//   if (result == null) {
//     for (var i = 0; i < MEHistograms.length; i++) {
//       MEHistograms[i].clear()
//       traces.push({
//         x: [0],
//         y: [0],
//         type: 'scatter',
//         name: ''
//       })
//     }
//     $('#HistogramWarning')[0].classList.add('d-none')
//   } else {
//     var configuration = result['Data']['MDIQKDEncoding']['Configuration']
//     var xs = linspace(0, configuration['Period'] / 1000.0, configuration[
//       'BinCount'])
//     var histogramXsMatched = true
//
//     var meData = result['Data']['MDIQKDEncoding']
//     for (var i = 0; i < MEConfigs.length; i++) {
//       var hisIs = MEConfigs[i][2]
//       for (var j = 0; j < hisIs.length; j++) {
//         var hisKey = MEHistogramKeys[hisIs[j]]
//         var his = meData[hisKey]
//         MEHistograms[i].append(xs, his)
//       }
//       traces.push({
//         x: MEHistograms[i].xs,
//         y: MEHistograms[i].ys,
//         type: 'scatter',
//         name: 'Trace',
//         line: {
//           color: '#2874A6',
//         }
//       })
//     }
//     for (var i = 0; i < MEHistograms.length; i++) {
//       histogramXsMatched &= MEHistograms[i].xsMatch
//     }
//     listener('HistogramXsMatched', histogramXsMatched)
//
//     // deal with reports
//     updateReports(result, MEHistograms)
//   }
//   for (var i = 0; i < MEConfigs.length; i++) {
//     layout['title'] = MEConfigs[i][0]
//     layout['yaxis']['range'] = [0, Math.max(...traces[i]['y']) * 1.05]
//     div = MEConfigs[i][1]
//     data = fillTrace.concat([traces[i]])
//     Plotly.react(div, data, layout, {
//       displaylogo: false,
//       // responsive: true
//     })
//     Plotly.redraw(div)
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
//   if (!invalid) fetcher.updateIntegralData(beginTime, endTime, isToNow)
// }
//
// function onSelectionIntegral(isIntegral) {
//   $("#selection-instant").attr("class", isIntegral ? "btn btn-secondary" :
//     "btn btn-success")
//   $("#selection-integral").attr("class", isIntegral ? "btn btn-success" :
//     "btn btn-secondary")
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
//
// function listener(event, arg) {
//   if (event == 'FetchTimeDelta') {
//     fetchTimeDelta = arg
//     if (fetchTimeDelta > 3000) {
//       $('#HistogramWarning')[0].classList.remove('d-none')
//       $('#HistogramWarningContent').html("The most recent data was fetched " +
//         parseInt(fetchTimeDelta / 1000) + " s ago.")
//     } else {
//       $('#HistogramWarning')[0].classList.add('d-none')
//     }
//   } else if (event == 'FetchingProgress') {
//     progress = parseInt(arg * 100)
//     $('#FetchingProgress').attr('style',
//       'background-image: linear-gradient(to right, #BDE6FF ' + (progress) +
//       '%, #F8F9FC ' + (progress) + '%)')
//   } else if (event == 'FetchingNumber') {
//     if (arg == null) {
//       $('#FetchNumberContent').html('')
//       $('#FetchNumber')[0].classList.add('d-none')
//     } else {
//       integralFetchedDataCount = arg[0]
//       integralTotalDataCount = arg[1]
//       integralTime = arg[2]
//       content = integralTotalDataCount + ' items (in ' + integralTime + ' s)'
//       if (integralFetchedDataCount < integralTotalDataCount) content =
//         integralFetchedDataCount + ' / ' + content
//       $('#FetchNumber')[0].classList.remove('d-none')
//       $('#FetchNumberContent').html(content)
//     }
//   } else if (event == 'HistogramXsMatched') {
//     if (!arg) {
//       $('#HistogramError')[0].classList.remove('d-none')
//       $('#HistogramErrorContent').html("Histogram Config Not Matched.")
//     } else {
//       $('#HistogramError')[0].classList.add('d-none')
//     }
//   } else if (event == 'TooManyRecords') {
//     if (arg) {
//       $('#TooManyRecordsError')[0].classList.remove('d-none')
//       $('#TooManyRecordsErrorContent').html("Too Many Records.")
//     } else {
//       $('#TooManyRecordsError')[0].classList.add('d-none')
//     }
//   } else {
//     console.log(event + ', ' + arg);
//   }
// }
//
function initDeviceStatusPanel() {
  temp = $('#DeviceStatusPaneTemp')

  function addDeviceStatusPane(title, id) {
    newItem = temp.clone(true)
    newItem.removeClass('d-none')
    newItem.find('.DPTT').html(title)
      //     newItem.find('.DPTC').attr('id', id)
    newItem.find('.ICSI').attr('id', 'ICSI_' + id)
    newItem.find('.ICSL').attr('for', 'ICSI_' + id)
    $('#DeviceStatusPanel').append(newItem)
  }
  addDeviceStatusPane('TDCService PostProcess', 'TDCPP')
  addDeviceStatusPane('TDCService LocalStore', 'TDCLS')
  addDeviceStatusPane('ADCMonitor Store', 'ADCS')
  temp.remove()
}

// function calculateRegionValues(result, histograms) {
//   regionValues = {}
//   regionWidths = markPoints.map(markPoint => markPoint[1] - markPoint[0])
//   MEConfigs.slice(0, 6).map((config, i) => {
//     regionValue = markPoints.map(markPoint => {
//       start = markPoint[0]
//       stop = markPoint[1]
//       return histograms[i].xs.zip(histograms[i].ys).filter(z =>
//         z[0] >= start && z[0] < stop).map(z => z[1]).sum()
//     })
//     correspondingPulseCount = config[2].map(r => result['Data'][
//       'MDIQKDEncoding'
//     ][
//       'Pulse Count of RandomNumber[' + r + ']'
//     ]).sum()
//     return regionValue.map((v, i) => v / regionWidths[i]).concat([
//       correspondingPulseCount
//     ])
//   }).map((v, i) => regionValues[MEConfigs[i][0]] = v)
//   return regionValues
// }
//
// async function updateReports(result, histograms) {
//   var risesPromise = ['Z 0', 'Z 1', 'Alice Delay', 'Bob Delay'].map(key => {
//     var his = MEHistograms[MEConfigs.map(c => c[0]).indexOf(key)]
//     return worker.Algorithm_Fitting.riseTimeFit(his.xs, his.ys)
//   })
//
//   var regionValues = calculateRegionValues(result, MEHistograms)
//   var pulseExtinctionRatio = (regionValues['All Pulses'][0] + regionValues[
//     'All Pulses'][1]) / (regionValues['All Pulses'][2]) / 2
//   var vacuumsCountRate = (regionValues['Vacuum'][0] + regionValues['Vacuum'][1]) /
//     regionValues['Vacuum'][3]
//   var Z0CountRate = (regionValues['Z 0'][0] + regionValues['Z 0'][1]) /
//     regionValues['Z 0'][3]
//   var Z1CountRate = (regionValues['Z 1'][0] + regionValues['Z 1'][1]) /
//     regionValues['Z 1'][3]
//   var XCountRate = (regionValues['X'][0] + regionValues['X'][1]) /
//     regionValues['X'][3]
//   var YCountRate = (regionValues['Y'][0] + regionValues['Y'][1]) /
//     regionValues['Y'][3]
//
//   $('#PER').html((10 * Math.log10(pulseExtinctionRatio)).toFixed(3) + ' dB')
//   $('#VI').html((10 * Math.log10(vacuumsCountRate / (Z0CountRate))).toFixed(2) +
//     ' dB')
//   $('#XI').html((XCountRate / Z0CountRate).toFixed(3))
//   $('#YI').html((YCountRate / Z0CountRate).toFixed(3))
//   $('#ZZ').html((Z0CountRate / Z1CountRate).toFixed(3))
//   $('#Z0ER').html((regionValues['Z 0'][1] / regionValues['Z 0'][0] * 100)
//     .toFixed(3) + '%')
//   $('#Z1ER').html((regionValues['Z 1'][0] / regionValues['Z 1'][1] * 100)
//     .toFixed(3) + '%')
//
//   var r = await Promise.all(risesPromise)
//   var doit = ['Z0', 'Z1', 'A', 'B'].map((key, i) => {
//     $('#' + key + 'R').html(r[i].toFixed(3) + ' ns')
//   })
// }
