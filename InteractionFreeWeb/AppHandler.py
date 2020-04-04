from tornado import web
import os


class IFAppHandler(web.RequestHandler):
    def get(self, name):
        if not os.path.exists('app/{}'.format(name)): raise RuntimeError('404')
        self.render("app/main.html", name=name)


class IFAppResourceHandler(web.RequestHandler):
    def get(self, appName, resource):
        path = 'app/{}/{}'.format(appName, resource)
        if not os.path.exists(path): raise RuntimeError('404')
        self.render(path)
