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
    ]
    settings = {
        'debug': True,
        'static_path': 'static',
        'ui_modules': uimodules
    }
    app = web.Application(handlers_array, **settings)
    app.listen(webPort)

    # worker1 = IFWorker(brokerURL, serviceName='TestService', serviceObject=None,
    #                    interfaces=['TestInterface 1', 'TestInterface 2'], timeout=5)
    # worker2 = IFWorker(brokerURL, serviceName='TestService2', serviceObject=None,
    #                    interfaces=['TestInterface 1', 'TestInterface 2'], timeout=1)
    # worker3 = IFWorker(brokerURL, serviceName='TestService3', serviceObject=None,
    #                    interfaces=['TestInterface 1', 'TestInterface 2'], timeout=1)

    fdSer = IFWorker(brokerURL, serviceName='IFLocalFileMeta', serviceObject=FileDistributor(
        IFLocalFilesPath, '/IFLocalFiles'.format(webHost, webPort)))
    # ArduinoZMQBridge.start()

    IFLoop.join()