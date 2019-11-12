import tornado.ioloop
import tornado.web
from github_access import list_modules, clone


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class ModuleHandler(tornado.web.RequestHandler):
    def get(self, slug):
        if slug == "list":  # list all available modules
            modules = list_modules()
            self.write({'type': 'list_modules',
                        'modules': modules})
        elif slug == "download": # download module given by query param 'name'
            module_to_download = self.get_argument('name', None)  # TODO handle input of wrong module name (BaseModule?)
            print("Installing Module: " + module_to_download)
            success = clone(module_to_download)  # download module
            self.write({'type': 'installation_response',
                        'module': module_to_download,
                        'success': success})


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/modules/([a-zA-Z\-0-9\.:,_]+)", ModuleHandler),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css/"})
    ])


if __name__ == '__main__':
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
