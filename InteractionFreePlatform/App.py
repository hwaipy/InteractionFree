from tornado import web
from IFBroker import IFBroker
from IFWorker import IFWorker
from IFCore import IFLoop
from Bridge import WebSocketZMQBridgeHandler
from AppHandler import IFAppHandler, IFAppResourceHandler
import UIModules as uimodules
from IFLocalFileService import FileDistributor
from MongoDBContext import MongoDBContext
from Config import Config

# class IndexHandler(web.RequestHandler):
#     def get(self):
#         # self.render("static/index.html")
#         return IFAppHandler(self.application, self.request).get('main')

if __name__ == '__main__':
    brokerHost = Config['IFBroker'].Address.asString()
    brokerPort = Config['IFBroker'].Port.asInt()
    brokerURL = 'tcp://{}:{}'.format(brokerHost, brokerPort)
    webHost = Config['Web'].Address.asString()
    webPort = Config['Web'].Port.asInt()
    IFLocalFilesPath = Config['IFLocal'].FilePath.asString()

    broker = IFBroker('tcp://*:{}'.format(brokerPort))

    handlers_array = [
        (r'/', IFAppHandler),
        (r'/ws', WebSocketZMQBridgeHandler),
        (r'/app/(.+?)/(.+)', IFAppResourceHandler),
        (r'/app/(.+)', IFAppHandler),
        (r"/IFLocalFiles/(.*)", web.StaticFileHandler, {'path': IFLocalFilesPath}),
        (r'/sfs/(.+)', web.StaticFileHandler, {"path": "E:/FTP/Temp"}),
        (r"/(.+)", web.StaticFileHandler, {'path': 'static'}),
        (r'/(favicon.ico)', web.StaticFileHandler, {"path": "static"}),
    ]
    settings = {
        'debug': False,
        'static_path': 'static',
        'ui_modules': uimodules,
        # 'default_handler_class': NotFoundHandler
    }
    app = web.Application(handlers_array, **settings)
    app.listen(webPort)

    fdSer = IFWorker(brokerURL, serviceName='IFLocalFileMeta', serviceObject=FileDistributor(
        IFLocalFilesPath, '/IFLocalFiles'.format(webHost, webPort)))
    stSer = IFWorker(brokerURL, serviceName='Storage', serviceObject=MongoDBContext.MongoDBContext.IFData.storage)

    # ArduinoZMQBridge.start()

    # d1 = IFWorker(brokerURL).Storage.range('TDCLocal', '', '')
    # print(d1)
    # from datetime import datetime, tzinfo
    # import time
    # from dateutil import tz
    #
    # NYC = tz.gettz('Europe / Berlin')
    # print(datetime.fromtimestamp(time.time(), NYC))
    # print(d1['Data'].keys())
    # d2 = IFWorker(brokerURL).Storage.latest('TDCLocal', time1)
    # print(d2)
    # d3 = IFWorker(brokerURL).Storage.latest('TDCLocal', '2020-05-04 00:21:21.605')
    # print(d3)

    IFLoop.join()
