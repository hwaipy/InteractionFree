class Histogram {
  constructor() {
    this.xs = null
    this.xsMatch = true
    this.ys = null
  }

  update(xs, ys) {
    this.xs = xs
    this.ys = ys
    this.xsMatch = true
  }

  clear() {
    this.xs = null
    this.ys = null
    this.xsMatch = true
  }

  append(xs, ys) {
    if (this.xs == null) {
      this.xs = xs
      this.ys = new Array(ys.length)
      for (var i = 0; i < ys.length; i++) {
        this.ys[i] = 0
      }
    } else {
      if (!_.isEqual(this.xs, xs)) {
        this.xsMatch = false
      }
    }
    for (var i = 0; i < ys.length; i++) {
      this.ys[i] += ys[i]
    }
  }

  genXs(start, stop, num) {
    if (num < 2) {
      return num === 1 ? [start] : [];
    }
    var i, ret = Array(num);
    num--;
    for (i = num; i >= 0; i--) {
      ret[i] = (i * stop + (num - i) * start) / num;
    }
    return ret;
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

function parseSimpleDate(str) {
  date = new Date()
  str = str.replaceAll("：", ":")
  var pattern = new RegExp(
    "^((((([0-9]+)-)?([0-9]+))-)?([0-9]+) )?([0-9]+):([0-9]+)(:([0-9]+))?$")
  r = pattern.exec(str)
  if (r == null) return null
  hour = r[8]
  min = r[9]
  day = r[7]
  month = r[6]
  year = r[5]
  second = r[11]

  if (year) {
    currentYear = "" + date.getFullYear()
    if (year.length < currentYear.length) {
      year = currentYear.substring(0, currentYear.length - year.length) + year
    }
    date.setFullYear(year)
  }
  if (month) date.setMonth(month - 1)
  if (day) date.setDate(day)
  date.setHours(hour)
  date.setMinutes(min)
  if (second) date.setSeconds(second)
  return date
}

function dateToString(date) {
  year = '' + date.getFullYear()
  month = '' + (date.getMonth() + 1)
  day = '' + date.getDate()
  hour = '' + date.getHours()
  minute = '' + date.getMinutes()
  second = '' + date.getSeconds()
  return year + '-' +
    (month.length < 2 ? '0' + month : month) + '-' +
    (day.length < 2 ? '0' + day : day) + ' ' +
    (hour.length < 2 ? '0' + hour : hour) + ':' +
    (minute.length < 2 ? '0' + minute : minute) + ':' +
    (second.length < 2 ? '0' + second : second)
}

String.prototype.replaceAll = function(s1, s2) {
  return this.replace(new RegExp(s1, "gm"), s2);
}

class TDCStorageStreamFatcher {
  constructor(worker, collection, updateInterval, filter, ploter, listener) {
    this.worker = worker
    this.collection = collection
    this.updateInterval = updateInterval
    this.updateRangedResultInterval = 50
    this.lastTime = null
    this.mode = 'Instant' // modes: Instant, Integral, IntegralContinues
    this.filter = filter
    this.fetchID = 0
    this.ploter = ploter
    this.integralTime = 0
    this.integralBeginTime = null
    this.integralEndTime = null
    this.integralMostRecentTime = null
    this.integralFetchedDataCount = 0
    this.integralTotalDataCount = 0
    this.integralContinuesHasNew = false
    this.listener = listener
    this.rangedResultQueue = []
    this.ploter(null, false)
  }

  start() {
    this.update()
    this.updateRangedResult()
  }

  update() {
    var __this = this
    if (this.mode == 'Instant' || this.mode == 'IntegralContinues') {
      var fetchID = this.fetchID
      worker.request("Storage", "latest", [this.collection, this.lastTime, this.filter], {},
        function(result) {
          if (fetchID == __this.fetchID) {
            if (result != null) {
              __this.lastTime = result['FetchTime'];
              if (__this.mode == 'Instant' || __this.mode == 'IntegralContinues') {
                __this.updateResult(result, fetchID, 'update')
              }
            }
            if (__this.mode == 'IntegralContinues') {
              __this.integralTime = parseInt((new Date().getTime() - __this.integralBeginTime.getTime())/1000)
              if (result != null){
                __this.integralTotalDataCount += 1
                __this.integralFetchedDataCount += 1
              }
            }
            __this.updateFetchingInfo()
          }
        },
        function(error) {
          console.log("Error: " + error)
        }
      )
    }
    this.updateFetchingInfo()
    setTimeout(this.update.bind(this), this.updateInterval)
  }

  range(beginTime, endTime) {
    var __this = this
    var fetchID = this.fetchID
    this.integralTime = parseInt((endTime.getTime() - beginTime.getTime())/1000)
    worker.request("Storage", "range", [this.collection, this.dateToISO(beginTime), this.dateToISO(endTime), 'FetchTime', this.filter], {},
      function(result) {
        __this.integralTotalDataCount += result.length
        for (var i = 0; i < result.length; i++) {
          worker.request("Storage", "get", [__this.collection, result[i]['_id'], __this.filter], {},
            function(result) {
              __this.rangedResultQueue.push([fetchID, result])
            },
            function(error) {
              console.log("Error: " + error)
            })
          __this.integralMostRecentTime = new Date();
          __this.integralMostRecentTime.setTime(Date.parse(result[i]['FetchTime']))
        }
      },
      function(error) {
        console.log("Error: " + error)
      }
    )
  }

  updateRangedResult() {
    if (this.rangedResultQueue.length > 0) {
      var resultSet = this.rangedResultQueue.shift()
      if (resultSet[0] == this.fetchID) {
        this.updateResult(resultSet[1])
        this.integralFetchedDataCount += 1
        this.updateFetchingInfo()
      }
    }
    setTimeout(this.updateRangedResult.bind(this), this.rangedResultQueue.length > 0 ? 0 : this.updateRangedResultInterval)
  }

  updateResult(result) {
    this.ploter(result, this.mode != 'Instant')
  }

  updateFetchingInfo() {
    // Check if display no data warning
    var fetchTimeDelta = 0
    if (this.mode == 'Instant') {
      fetchTimeDelta = new Date().getTime() - Date.parse(this.lastTime)
    } else if (this.mode == 'IntegralContinues') {
      if (this.integralContinuesHasNew) {
        fetchTimeDelta = new Date().getTime() - Date.parse(this.lastTime)
      } else {
        if (this.integralFetchedDataCount == this.integralTotalDataCount && this.integralMostRecentTime != null) {
          fetchTimeDelta = new Date().getTime() - this.integralMostRecentTime.getTime()
        }
      }
    }
    if (this.mode == 'Integral' || this.mode == 'IntegralContinues') {
      if (this.integralFetchedDataCount == 0) {
        fetchTimeDelta = 0
      }
    }
    this.listener('FetchTimeDelta', fetchTimeDelta);

    // Set prograss
    if (this.integralTotalDataCount > 0 && this.integralFetchedDataCount < this.integralTotalDataCount) {
      this.listener('FetchingProgress', this.integralFetchedDataCount * 1.0 / this.integralTotalDataCount)
    } else {
      this.listener('FetchingProgress', 0.0)
    }

    // Set FetchNumber
    if (this.mode == 'Integral' || this.mode == 'IntegralContinues') {
      this.listener('FetchingNumber', [this.integralFetchedDataCount, this.integralTotalDataCount, this.integralTime])
    } else {
      this.listener('FetchingNumber', null)
    }
  }

  changeMode(mode) {
    if (mode == this.mode) return
    if (mode != 'Instant' && mode != 'Integral' && mode !=
      'IntegralContinues' && mode != 'Stop') {
      console.log('Bad mode: ' + mode)
      return
    }
    this.mode = mode
    this.integralTime = 0
    this.integralTotalDataCount = 0
    this.integralFetchedDataCount = 0
    this.integralContinuesHasNew = false
    if (mode == 'Instant') this.lastTime = 0
    if (mode != 'Stop') this.fetchID += 1
    this.ploter(null, false)
  }

  updateIntegralData(beginTime, endTime, isToNow) {
    this.integralBeginTime = beginTime
    this.integralEndTime = endTime
    this.changeMode("Stop")
    this.changeMode(isToNow ? "IntegralContinues" : "Integral")
    if(isToNow) this.lastTime = this.dateToISO(endTime)
    this.range(beginTime, endTime)
  }

  dateToISO(date) {
    return dateToString(date).replace(' ', 'T') + '.000000+08:00'
  }
}
