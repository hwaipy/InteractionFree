from tornado import web
import os
import configparser


class IFAppHandler(web.RequestHandler):
    def get(self, name=None):
        if name == None: name = 'main'
        config = configparser.ConfigParser()
        config.read('app/{}/{}.ini'.format(name, name))
        displayedName = config.get('App', 'DisplayedName', fallback=name)
        if not os.path.exists('app/{}'.format(name)): raise web.HTTPError(404)
        self.render("app/main.html", name=name, displayedName=displayedName)


class IFAppResourceHandler(web.RequestHandler):
    def get(self, appName, resource):
        path = 'app/{}/{}'.format(appName, resource)
        if not os.path.exists(path): raise web.HTTPError(404)
        self.render(path)

# class NotFoundHandler(web.RequestHandler):
#     def get(self, name=None):
#         print('get')
#
#     def prepare(self):  # for all methods
#         print('404')
#         raise web.HTTPError(
#             status_code=404,
#             reason="404!"
#         )
