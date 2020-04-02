from tornado import web
import os


class IFAppHandler(web.RequestHandler):
    def get(self, name):
        if not os.path.exists('app/{}'.format(name)): raise RuntimeError('404')
        self.render("app/main.html", name=name)


class IFAppResourceHandler(web.RequestHandler):
    def get(self, p, q):
        items = ["Item 1", "Item 2", "Item 3"]
        print('r')
        print(p)
        print(q)
        self.render("app/main.html", title="My title", items=items)
