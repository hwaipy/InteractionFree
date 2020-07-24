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
  initResultPanel()

  worker = await IFWorker(endpoint)

  filter = {
    'Data.Counter': 1,
    // 'Data.CoincidenceHistogram': 1,
    'Data.MDIQKDEncoding.Configuration': 1,
    'Data.MDIQKDEncoding.Configuration.SignalChannel': 1,
    'Data.MDIQKDEncoding.Configuration.TimeAliceChannel': 1,
    'Data.MDIQKDEncoding.Configuration.TimeBobChannel': 1,
    'Data.MDIQKDEncoding.Configuration.TriggerChannel': 1,
    'Data.MDIQKDEncoding.Configuration.Period': 1,
    'Data.MDIQKDEncoding.Configuration.BinCount': 1,
    'Data.MDIQKDEncoding.Pulse Count of RandomNumber[0]': 1,
    'Data.MDIQKDEncoding.Pulse Count of RandomNumber[1]': 1,
    'Data.MDIQKDEncoding.Pulse Count of RandomNumber[2]': 1,
    'Data.MDIQKDEncoding.Pulse Count of RandomNumber[3]': 1,
    'Data.MDIQKDEncoding.Pulse Count of RandomNumber[4]': 1,
    'Data.MDIQKDEncoding.Pulse Count of RandomNumber[5]': 1,
    'Data.MDIQKDEncoding.Pulse Count of RandomNumber[6]': 1,
    'Data.MDIQKDEncoding.Pulse Count of RandomNumber[7]': 1,
  }
  for (var i = 0; i < Object.keys(MEHistogramKeys).length; i++) {
    filter['Data.MDIQKDEncoding.' + MEHistogramKeys[Object.keys(
      MEHistogramKeys)[i]]] = 1
  }
  fetcher = new TDCStorageStreamFetcher(worker, collection, 500, filter,
    plot, listener)
  fetcher.start()
})

worker = null
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

MEHistogramKeys = {
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

markPoints = [
  [0.4, 1.4, '#F1E4C6'],
  [2.4, 3.4, '#D5E9D5'],
  [3.8, 4.0, '#D3E4EB']
]
fillTrace = []
for (var i = 0; i < markPoints.length; i++) {
  markPoint = markPoints[i]
  fillTrace.push({
    x: [markPoint[0], markPoint[0], markPoint[1], markPoint[1]],
    y: [-1e10, 1e10, 1e10, -1e10],
    fill: 'toself',
    type: 'scatter',
    mode: 'none',
    hoverinfo: 'none',
    fillcolor: markPoint[2],
  })
}

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
$('.MEViewPane').remove()

function plot(result, append) {
  var layout = {
    xaxis: {
      title: 'Time (ns)'
    },
    yaxis: {
      title: 'Count'
    },
    margin: {
      l: 50,
      r: 30,
      b: 50,
      t: 30,
      pad: 4
    },
    // width: 300,
    height: 250,
    showlegend: false,
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
    var configuration = result['Data']['MDIQKDEncoding']['Configuration']
    var xs = linspace(0, configuration['Period'] / 1000.0, configuration[
      'BinCount'])
    var histogramXsMatched = true

    if (!append) MEHistograms.map(h => h.clear())

    var meData = result['Data']['MDIQKDEncoding']
    for (var i = 0; i < MEConfigs.length; i++) {
      var hisIs = MEConfigs[i][2]
      for (var j = 0; j < hisIs.length; j++) {
        var hisKey = MEHistogramKeys[hisIs[j]]
        var his = meData[hisKey]
        MEHistograms[i].append(xs, his)
      }
      traces.push({
        x: MEHistograms[i].xs,
        y: MEHistograms[i].ys,
        type: 'scatter',
        name: 'Trace',
        line: {
          color: '#2874A6',
        }
      })
    }
    for (var i = 0; i < MEHistograms.length; i++) {
      histogramXsMatched &= MEHistograms[i].xsMatch
    }
    listener('HistogramXsMatched', histogramXsMatched)

    // deal with reports
    updateReports(result, MEHistograms)
  }
  for (var i = 0; i < MEConfigs.length; i++) {
    layout['title'] = MEConfigs[i][0]
    layout['yaxis']['range'] = [0, Math.max(...traces[i]['y']) * 1.05]
    div = MEConfigs[i][1]
    data = fillTrace.concat([traces[i]])
    Plotly.react(div, data, layout, {
      displaylogo: false,
      // responsive: true
    })
    Plotly.redraw(div)
  }
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
      $('#HistogramWarningContent').html("The most recent data was fetched " +
        parseInt(fetchTimeDelta / 1000) + " s ago.")
    } else {
      $('#HistogramWarning')[0].classList.add('d-none')
    }
  } else if (event == 'FetchingProgress') {
    progress = parseInt(arg * 100)
    $('#FetchingProgress').attr('style',
      'background-image: linear-gradient(to right, #BDE6FF ' + (progress) +
      '%, #F8F9FC ' + (progress) + '%)')
  } else if (event == 'FetchingNumber') {
    if (arg == null) {
      $('#FetchNumberContent').html('')
      $('#FetchNumber')[0].classList.add('d-none')
    } else {
      integralFetchedDataCount = arg[0]
      integralTotalDataCount = arg[1]
      integralTime = arg[2]
      content = integralTotalDataCount + ' items (in ' + integralTime + ' s)'
      if (integralFetchedDataCount < integralTotalDataCount) content =
        integralFetchedDataCount + ' / ' + content
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
    console.log(event + ', ' + arg);
  }
}

function initResultPanel() {
  temp = $('#ResultPaneTemp')

  function addResultPane(div, title, id) {
    newItem = temp.clone(true)
    newItem.removeClass('d-none')
    newItem.addClass('border-left-info')
    newItem.find('.DPTT').html(title)
    newItem.find('.DPTC').attr('id', id)
    $('#' + div).append(newItem)
  }
  addResultPane('ResultPanel_Intensity', 'Pulse Extinction Ratio: ', 'PER')
  addResultPane('ResultPanel_Intensity', 'Vacuum Intensity: ', 'VI')
  addResultPane('ResultPanel_Intensity', 'X Intensity: ', 'XI')
  addResultPane('ResultPanel_Intensity', 'Y Intensity: ', 'YI')
  addResultPane('ResultPanel_Intensity', 'Z 0 / Z 1: ', 'ZZ')
  addResultPane('ResultPanel_Error', 'Z 0 Error Rate: ', 'Z0ER')
  addResultPane('ResultPanel_Error', 'Z 1 Error Rate: ', 'Z1ER')
  addResultPane('ResultPanel_Rise', 'Z 0 Rise: ', 'Z0R')
  addResultPane('ResultPanel_Rise', 'Z 1 Rise: ', 'Z1R')
  addResultPane('ResultPanel_Rise', 'Alice Rise: ', 'AR')
  addResultPane('ResultPanel_Rise', 'Bob Rise: ', 'BR')
  temp.remove()
}

function calculateRegionValues(result, histograms) {
  regionValues = {}
  regionWidths = markPoints.map(markPoint => markPoint[1] - markPoint[0])
  MEConfigs.slice(0, 6).map((config, i) => {
    regionValue = markPoints.map(markPoint => {
      start = markPoint[0]
      stop = markPoint[1]
      return histograms[i].xs.zip(histograms[i].ys).filter(z =>
        z[0] >= start && z[0] < stop).map(z => z[1]).sum()
    })
    correspondingPulseCount = config[2].map(r => result['Data'][
      'MDIQKDEncoding'
    ][
      'Pulse Count of RandomNumber[' + r + ']'
    ]).sum()
    return regionValue.map((v, i) => v / regionWidths[i]).concat([
      correspondingPulseCount
    ])
  }).map((v, i) => regionValues[MEConfigs[i][0]] = v)
  return regionValues
}

async function updateReports(result, histograms) {
  var risesPromise = ['Z 0', 'Z 1', 'Alice Delay', 'Bob Delay'].map(key => {
    var his = MEHistograms[MEConfigs.map(c => c[0]).indexOf(key)]
    return worker.Algorithm_Fitting.riseTimeFit(his.xs, his.ys)
  })

  var regionValues = calculateRegionValues(result, MEHistograms)
  var pulseExtinctionRatio = (regionValues['All Pulses'][0] + regionValues[
    'All Pulses'][1]) / (regionValues['All Pulses'][2]) / 2
  var vacuumsCountRate = (regionValues['Vacuum'][0] + regionValues['Vacuum'][1]) /
    regionValues['Vacuum'][3]
  var Z0CountRate = (regionValues['Z 0'][0] + regionValues['Z 0'][1]) /
    regionValues['Z 0'][3]
  var Z1CountRate = (regionValues['Z 1'][0] + regionValues['Z 1'][1]) /
    regionValues['Z 1'][3]
  var XCountRate = (regionValues['X'][0] + regionValues['X'][1]) /
    regionValues['X'][3]
  var YCountRate = (regionValues['Y'][0] + regionValues['Y'][1]) /
    regionValues['Y'][3]

  $('#PER').html((10 * Math.log10(pulseExtinctionRatio)).toFixed(3) + ' dB')
  $('#VI').html((10 * Math.log10(vacuumsCountRate / (Z0CountRate))).toFixed(2) +
    ' dB')
  $('#XI').html((XCountRate / Z0CountRate).toFixed(3))
  $('#YI').html((YCountRate / Z0CountRate).toFixed(3))
  $('#ZZ').html((Z0CountRate / Z1CountRate).toFixed(3))
  $('#Z0ER').html((regionValues['Z 0'][1] / regionValues['Z 0'][0] * 100)
    .toFixed(3) + '%')
  $('#Z1ER').html((regionValues['Z 1'][0] / regionValues['Z 1'][1] * 100)
    .toFixed(3) + '%')

  var r = await Promise.all(risesPromise)
  var doit = ['Z0', 'Z1', 'A', 'B'].map((key, i) => {
    $('#' + key + 'R').html(r[i].toFixed(3) + ' ns')
  })
}
