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
  if(str == 'now') return date
  var pattern = new RegExp("^((((([0-9]+)-)?[0-9]+)-)?([0-9]+) )?([0-9]+):([0-9]+)(:([0-9]+))?$")
  r = pattern.exec(str)
  if (r == null) return null
  console.log(r)
  hour = r[7]
  min = r[8]
  date.setHours(hour)
  date.setMinutes(min)
console.log(date);
  return date
}
