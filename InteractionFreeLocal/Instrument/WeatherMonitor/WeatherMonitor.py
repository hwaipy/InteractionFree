import urllib.request
from interactionfreepy import IFWorker
from datetime import datetime

if __name__ == '__main__':
    print('in w m')

    site = ['Shanghai', 'SH', 121.542, 31.126, 0]

    url = "http://www.7timer.info/bin/astro.php?lon={}&lat={}&lang=zh-CN&ac=0&unit=metric&tzshift={}".format(site[2], site[3], site[4])

    print(url)

    contents = urllib.request.urlopen(url).read()

    print(contents)

    worker = IFWorker('tcp://127.0.0.1:224', 'WeatherMonitor')
    worker.Storage.append('Weathers', {'Location': 'SH', 'data': contents}, datetime.now().isoformat())
