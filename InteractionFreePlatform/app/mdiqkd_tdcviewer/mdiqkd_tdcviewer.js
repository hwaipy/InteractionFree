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
  tdcService = parameters['tdcservice'] || null
  collection = parameters['collection'] || null
  tdcConfiger = null

  worker = await IFWorker(endpoint)

  if (tdcService != null) {
      collection = await worker[tdcService].getStoraCollectionName()
      tdcConfiger = new TDCConfiger(worker, tdcService)
      tdcConfiger.start()
      startFetching(worker, collection)
  } else startFetching(worker, collection)
})

class TDCConfiger {
  constructor(worker, tdcService) {
    this.worker = worker
    this.tdcService = tdcService
    this.delayPaneInited = false
    this.editingField = null
    this.recentDelays = null
  }

    start() {
    this.updateDelays()
  }

  async updateDelays() {
    this.recentDelays = await worker[tdcService].getDelays()
    if (!this.delayPaneInited) {
      initControlPanel(this.recentDelays.length)
      this.delayPaneInited = true
    }
    for (var i = 0; i < this.recentDelays.length; i++) {
      if ('' + i != this.editingField) $('#DPTI_' + i).val('' + this.recentDelays[i] / 1000.0)
    }
    var mhResult = await worker[tdcService].getAnalyserConfiguration('MultiHistogram')
    if (this.editingField != 'Sync') $('#DPTI_Sync').val(mhResult['Sync'])
    if (this.editingField != 'ViewStart') $('#DPTI_ViewStart').val(mhResult['ViewStart'] / 1000.0)
    if (this.editingField != 'ViewStop') $('#DPTI_ViewStop').val(mhResult['ViewStop'] / 1000.0)
    if (this.editingField != 'BinCount') $('#DPTI_BinCount').val(mhResult['BinCount'])
    if (this.editingField != 'Divide') $('#DPTI_Divide').val(mhResult['Divide'])
    var signals = mhResult['Signals']
    for(var i = 0; i < this.recentDelays.length; i++) {
      $('#CC_' + i).prop("checked", signals.includes(i))
    }
    setTimeout(this.updateDelays.bind(this), 1100)
  }

  editing(id) {
    this.editingField = id.split('_')[1]
  }

  edited(id) {
    this.editingField = null
    var editedField = id.split('_')[1]
    var editedValue = $('#' + id).val()
    if (!isNaN(parseInt(editedField))) {
      // edited a channel delay
      var editedChannel = parseInt(editedField)
      var editedDelay = parseFloat(editedValue)
      if (isNaN(editedDelay)) editedDelay = this.recentDelays[editedChannel]
      $('#' + id).val('' + editedDelay)
      worker[tdcService].setDelay(editedChannel, parseInt(editedDelay * 1000))
    } else {
      // edited a MultiHistogram config
      var config = {}
      if (editedField == 'Sync') {
        config['Sync'] = parseInt(editedValue)
      }
      if (editedField == 'ViewStart' || editedField == 'ViewStop') {
        config[editedField] = parseFloat(editedValue) * 1000.0
      }
      if (editedField == 'BinCount' || editedField == 'Divide') {
        config[editedField] = parseInt(editedValue)
      }
      worker[tdcService].configureAnalyser('MultiHistogram', config)
    }
  }
}

function startFetching(worker, collection) {
  fetcher = new TDCStorageStreamFetcher(worker, collection, 500, {
    'Data.Counter': 1,
    'Data.MultiHistogram': 1
  }, plot, listener)
  fetcher.start()
}

function initControlPanel(channelNum) {
  temp = $('#DelayPaneTemp')
  function addPane(div, title, tail, border, div_id, input_id, check_id) {
    newItem = temp.clone(true)
    newItem.removeClass('d-none')
    newItem.addClass('border-left-' + border)
    newItem.attr('id', 'DelayPane_' + i)
    $('#' + div).append(newItem)
    newItem.find('.DPTT').html(title)
    newItem.find('.DPTTi').html(tail)
    newItem.find('.DPTI').attr('id', input_id)
    if (check_id != null && check_id.length > 0) {
      newItem.find('.ChannelCheckDiv').removeClass('d-none')
      newItem.find('.ChannelCheck').attr('id', check_id)
    }
  }
  for(var i = 0; i < channelNum; i++) {
    addPane('DelayPanel', 'CH ' + (i < 10 ? '0' : '') + i, 'ns', 'info', 'DelayPanel_' + i, 'DPTI_' + i, 'CC_' + i)
  }
  addPane('ViewPanel', 'Trigger', '', 'success', 'DelayPanel_Sync', 'DPTI_Sync')
  addPane('ViewPanel', 'From', 'ns', 'success', 'DelayPanel_ViewStart', 'DPTI_ViewStart')
  addPane('ViewPanel', 'To', 'ns', 'success', 'DelayPanel_ViewStop', 'DPTI_ViewStop')
  addPane('ViewPanel', 'Divide', '', 'success', 'DelayPanel_Divide', 'DPTI_Divide')
  addPane('ViewPanel', 'BinNum', '', 'success', 'DelayPanel_BinCount', 'DPTI_BinCount')
  // addPane('ViewPanel', 'Signals', '', 'success', 'DelayPanel_Signals', 'DPTI_Signals')
  temp.remove()
  $('#ControlBoardCard').removeClass('d-none')
}

function onTDCConfigInputFocus(id, isBlur) {
  if (isBlur) tdcConfiger.edited(id)
  else tdcConfiger.editing(id)
}

function onChannelCheckChange(id) {
  signals = []
  $('.ChannelCheck').each(function(index){
    if ($(this).attr('id')) {
      if ($(this).prop('checked')) {
        signals.push(parseInt($(this).attr('id').split('_')[1]))
      }
    }
  })
  worker[tdcService].configureAnalyser('MultiHistogram', {'Signals': signals})
}

TDCHistograms = new Array(32)
for (var i = 0; i < TDCHistograms.length; i++) {
  TDCHistograms[i] = new Histogram()
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
    for (var i = 0; i < TDCHistograms.length; i++) {
      TDCHistograms[i].clear()
    }
    traces.push({
      x: [0],
      y: [0],
      type: 'scatter',
      name: 'CH0'
    })
    $('#HistogramWarning')[0].classList.add('d-none')
  } else {
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
    var histogramXsMatched = true
    for (var i = 0; i < signalChannels.length; i++) {
      var channelNum = signalChannels[i]
      histogram = TDCHistograms[channelNum]
      if (append) histogram.append(xs, histograms[i])
      else histogram.update(xs, histograms[i])
      var channelNumStr = signalChannels[i].toString()
      if (channelNumStr.length == 1) channelNumStr = "0" + channelNumStr
      traces.push({
        x: histogram.xs,
        y: histogram.ys,
        type: 'scatter',
        name: 'CH' + channelNumStr
      })
      histogramXsMatched &= histogram.xsMatch
    }
    layout['uirevision'] = 'true'
    listener('HistogramXsMatched', histogramXsMatched)
  }
  Plotly.react('viewport', traces, layout, {
    displaylogo: false,
    // responsive: true
  })
  Plotly.redraw('viewport')
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
  $("#selection-instant").attr("class", isIntegral ? "btn btn-secondary" : "btn btn-success")
  $("#selection-integral").attr("class", isIntegral ? "btn btn-success" : "btn btn-secondary")
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
