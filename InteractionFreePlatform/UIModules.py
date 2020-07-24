from tornado import web


# class Top(web.UIModule):
#     def render(self, name):
#         print(name)
#         return self.render_string("dynamic/uimodules/top.html")
#
#
# class Imports(web.UIModule):
#     def render(self, name):
#         print('Importing ', name)
#         # print(self.())
#         return self.render_string("app/imports.html")


class AppContent(web.UIModule):
    def render(self, name):
        return self.render_string("app/{}/{}.html".format(name, name))

    # def javascript_files(self, name):
    #     # return None
    #     print(name)
    #
    #
    #     return ['/static/javascripts/IF.js']


class AppScript(web.UIModule):
    def render(self, name):
        return '<script type="text/javascript" src="/app/{}/{}.js"></script>'.format(name, name)
