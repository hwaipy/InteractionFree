$(document).ready(async function() {
  var endpoint = "ws://" + window.location.host + "/ws"
  var worker = await IFWorker(endpoint)

  var interval = 2000
  async function update() {
    try {
      var result = await worker.listServiceMeta()
      tableContent = serviceTableHead
      for (var i = 0; i < result.length; i++) {
        var row = generateTableRow(result[i][0], result[i][1], result[i][2],
          result[i][3])
        tableContent += row
      }
      $("#ServiceTable").html(tableContent)
    } catch(error) {
      console.log("Error: " + error)
    }
    setTimeout(update, interval)
  }
  update(interval)
});

serviceTableHead =
  '<thead><tr class="w3-light-grey"><th>Service</th><th>Interfaces</th><th>Address</th><th>On Time</th></tr></thead>';

function generateTableRow(service, address, interfaces, onTime) {
  return "<tr><td>" + service +
    "</td><td>" + formatInterfaces(interfaces) +
    "</td><td>" + formatAddress(address) +
    "</td><td>" + formatOnTime(onTime) + "</td></tr>";
}

function formatOnTime(onTime) {
  if (onTime / 86400 >= 2) return '' + Math.floor(onTime / 86400) + ' days'
  if (onTime / 86400 >= 1) return '' + Math.floor(onTime / 86400) + ' day'
  if (onTime / 3600 >= 2) return '' + Math.floor(onTime / 3600) + ' hours'
  if (onTime / 3600 >= 1) return '' + Math.floor(onTime / 3600) + ' hour'
  if (onTime / 60 >= 2) return '' + Math.floor(onTime / 60) + ' minutes'
  if (onTime / 60 >= 1) return '' + Math.floor(onTime / 60) + ' minute'
  if (onTime >= 2) return '' + Math.floor(onTime) + ' seconds'
  return '' + Math.floor(onTime) + ' second'
}

function formatAddress(address) {
  formattedAddress = ''
  for (var i = 0; i < address.length; i++) {
    var part = address[i].toString(16)
    if (part.length == 2) formattedAddress += part
    else formattedAddress += '0' + part
  }
  return formattedAddress.toUpperCase()
}

function formatInterfaces(interfaces) {
  result = ''
  for (var i = 0; i < interfaces.length; i++) {
    if (i > 0) result += ', '
    result += '<a href="/protocol/interface/' + interfaces[i] + '">' +
      interfaces[i] + '</a>'
  }
  return result
}
