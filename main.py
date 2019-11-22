import tornado.ioloop
import tornado.web
from github_access import list_modules, clone
from util import list_installed_modules, remove_module_files, get_config_path, load_config, write_config


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class ModuleHandler(tornado.web.RequestHandler):
    def get(self, slug):
        if slug == "list_available":  # list all available modules
            modules = list_modules()
            self.write({'type': 'list_available_modules',
                        'modules': modules})
        elif slug == "list_installed":  # list istalled modules
            modules = list_installed_modules()
            self.write({'type': 'list_installed_modules',
                        'installed_modules': modules})
        elif slug == "download":  # download module given by query param 'name'
            module_to_download = self.get_argument('name', None)  # TODO handle input of wrong module name (BaseModule?)
            print("Installing Module: " + module_to_download)
            success = clone(module_to_download)  # download module
            self.write({'type': 'installation_response',
                        'module': module_to_download,
                        'success': success})
        elif slug == "uninstall":  # uninstall module given by query param 'name'
            module_to_uninstall = self.get_argument('name', None)
            # TODO make sure this module is not running, or if running, stop it before deleting the files
            print('Uninstalling Module: ' + module_to_uninstall)
            success = remove_module_files(module_to_uninstall)
            self.write({'type': 'uninstallation_response',
                        'module': module_to_uninstall,
                        'success': success})


class ConfigHandler(tornado.web.RequestHandler):
    def get(self, slug):
        if slug == "view":
            module = self.get_argument("module_name", None)  # TODO handle input of wrong module name
            config_path = get_config_path(module)
            config = load_config(config_path)
            self.write({'type': 'view_config',
                        'config': config})

    def post(self, slug):
        if slug == "update":
            module = self.get_argument("module_name", None)  # TODO handle input of wrong module name
            config_path = get_config_path(module)
            new_config = tornado.escape.json_decode(self.request.body)
            write_config(config_path, new_config)


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/modules/([a-zA-Z\-0-9\.:,_]+)", ModuleHandler),
        (r"/configs/([a-zA-Z\-0-9\.:,_]+)", ConfigHandler),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css/"})
    ])


if __name__ == '__main__':
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
