from tornado import web
from IFBroker import IFBroker
from IFCore import IFLoop
from WebSocket import WebSocketZMQBridgeHandler
from AppHandler import IFAppHandler, IFAppResourceHandler
import UIModules as uimodules


class IndexHandler(web.RequestHandler):
    def get(self):
        # self.render("static/index.html")
        return IFAppHandler(self.application, self.request).get('main')


if __name__ == '__main__':
    broker = IFBroker('tcp://*:224')

    handlers_array = [
        (r'/', IndexHandler),
        (r'/ws', WebSocketZMQBridgeHandler),
        # (r'/app/main', IFAppHandler),
        # (r'/app/dashboard', IFAppHandler)
        (r'/app/(.+?)/(.+)', IFAppResourceHandler),
        (r'/app/(.+)', IFAppHandler),
    ]
    settings = {
        'debug': True,
        'static_path': 'static',
        'ui_modules': uimodules
    }
    app = web.Application(handlers_array, **settings)
    app.listen(8080)

    # worker1 = IFWorker("tcp://127.0.0.1:224", serviceName='TestService', serviceObject=None,
    #                    interfaces=['TestInterface 1', 'TestInterface 2'], timeout=1)
    # worker2 = IFWorker("tcp://127.0.0.1:224", serviceName='TestService2', serviceObject=None,
    #                    interfaces=['TestInterface 1', 'TestInterface 2'], timeout=1)
    # worker3 = IFWorker("tcp://127.0.0.1:224", serviceName='TestService3', serviceObject=None,
    #                    interfaces=['TestInterface 1', 'TestInterface 2'], timeout=1)

    IFLoop.join()
