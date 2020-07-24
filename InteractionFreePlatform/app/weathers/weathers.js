$(document).ready(function() {
  var parameterString = window.location.search
  if (parameterString.length > 0){
    parameterStrings = parameterString.split('?')[1].split('&')
    sites = []
    for(var i=0;i<parameterStrings.length;i++){
      paras = parameterStrings[i].split(',')
      sites.push([paras[0], paras[1], parseFloat(paras[2]), parseFloat(paras[3]), parseInt(paras[4])])
    }
  } else {
    sites = [
      ['Shanghai', 'SH', 121.542, 31.126, 0],
      ['Beijing', 'BJ', 116.3, 40, 0],
    ]
  }

  for(var i=0;i<sites.length;i++){
    site = sites[i]
    url = "http://www.7timer.info/bin/astro.php?lon="+site[2]+"&lat="+site[3]+"&lang=zh-CN&ac=0&unit=metric&tzshift="+site[4]+""
    $('#viewport').append($('#card_template')[0].innerHTML.split('VTR_ID').join(site[1]).split('VTR_HEADING').join(site[0]))
    $('#bufferport').append('<img id="ViewImg_' + site[1] + '" src="' + url + '" onload="imgLoaded(this.id)"></img>')
  }
});

function imgLoaded(id){
  id = id.split('ViewImg_')[1]
  console.log('loaded ' + id);
  $('#LoadingImg_'+id).addClass('w3-hide')
  var canvas = $('#ViewCanvas_'+id)
  canvas.removeClass('w3-hide')
  var ctx = canvas[0].getContext('2d');
  var img = document.getElementById('ViewImg_'+id)
  var actualWidth = img.naturalWidth
  var actualHeight = img.naturalHeight
  var scale = 1
  ctx.drawImage(img, 0, 0, actualWidth * scale, actualHeight * scale);

  ctx.fillStyle = "balck";
  ctx.fillRect(440, 0, 130, 30)
  ctx.font = "15px Arial Bold";
  ctx.fillStyle = "white";
  ctx.fillText(id, 452, 22)
  ctx.fillText("@Hwaipy", 500, 22)
}
