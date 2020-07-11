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
