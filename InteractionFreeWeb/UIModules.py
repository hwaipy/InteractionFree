from tornado import web


class Top(web.UIModule):
    def render(self, name):
        print(name)
        return self.render_string("dynamic/uimodules/top.html")


class Imports(web.UIModule):
    def render(self):
        return self.render_string("dynamic/uimodules/imports.html")


class AppContent(web.UIModule):
    def render(self, name):
        return self.render_string("app/{}/{}.html".format(name, name))
