from tornado import web


class AppContent(web.UIModule):
    def render(self, name):
        return self.render_string("app/{}/{}.html".format(name, name))


class AppScript(web.UIModule):
    def render(self, name):
        return '<script type="text/javascript" src="/app/{}/{}.js"></script>'.format(name, name)
