import tornado.ioloop
import tornado.web
import importlib
import sys
from CONSTANTS import MODULE_PACKAGE
from github_access import list_modules, clone
from util import list_installed_modules, remove_module_files, get_config_path, load_config, write_config, determine_free_port


servers = {}


class MainHandler(tornado.web.RequestHandler):
    """
    Serves the Frontend

    """

    def get(self):
        """
        GET request for the index.html page

        """

        self.render("index.html")


class ModuleHandler(tornado.web.RequestHandler):
    """
    Handles module architecture

    """

    def get(self, slug):
        """
        GET Request of /modules/[slug]

        slug can either be: list_available, list_installed, download, uninstall
            list_available: list all modules that can be installed from the remote repo
            list_installed: list all installed modules
            download: query param: 'module_name'
                    download a module from the remote repo
            uninstall: query param: 'module_name'
                    delete a module

        """

        if slug == "list_available":  # list all available modules
            modules = list_modules()
            self.write({'type': 'list_available_modules',
                        'modules': modules})
        elif slug == "list_installed":  # list istalled modules
            modules = list_installed_modules()
            self.write({'type': 'list_installed_modules',
                        'installed_modules': modules})
        elif slug == "download":  # download module given by query param 'name'
            module_to_download = self.get_argument('module_name', None)  # TODO handle input of wrong module name (BaseModule?)
            print("Installing Module: " + module_to_download)
            success = clone(module_to_download)  # download module
            self.write({'type': 'installation_response',
                        'module': module_to_download,
                        'success': success})
        elif slug == "uninstall":  # uninstall module given by query param 'name'
            module_to_uninstall = self.get_argument('module_name', None)

            # check the module is not running, and if, stop it before uninstalling
            if module_to_uninstall in servers:
                shutdown_module(module_to_uninstall)

            print('Uninstalling Module: ' + module_to_uninstall)
            success = remove_module_files(module_to_uninstall)
            self.write({'type': 'uninstallation_response',
                        'module': module_to_uninstall,
                        'success': success})


class ConfigHandler(tornado.web.RequestHandler):
    """
    Handles configs of modules

    """

    def get(self, slug):
        """
        GET request of /configs/view
            query param: 'module_name'
                get the config of the module given by module_name

        """

        if slug == "view":
            module = self.get_argument("module_name", None)  # TODO handle input of wrong module name
            config_path = get_config_path(module)
            config = load_config(config_path)
            self.write({'type': 'view_config',
                        'module': module,
                        'config': config})

    def post(self, slug):
        """
        POST request of /configs/update
            query param: 'module_name'
            http body: json
                changes the config of the module given by module_name to the json in the http body

        """

        if slug == "update":
            module = self.get_argument("module_name", None)  # TODO handle input of wrong module name
            config_path = get_config_path(module)
            new_config = tornado.escape.json_decode(self.request.body)
            write_config(config_path, new_config)


class ExecutionHandler(tornado.web.RequestHandler):
    """
    handles execution and stopping of modules

    """

    def get(self, slug):
        """
        GET request of /execution/[slug]

        slug can eiter be: start, stop
            start: query param: 'module_name'
                start a module
            stop: query param: 'module_name'
                stop a module

        """

        if slug == "start":
            module_to_start = self.get_argument("module_name", None)
            if module_to_start not in servers:
                spec = importlib.util.find_spec(".main", MODULE_PACKAGE + module_to_start)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_to_start] = module
                spec.loader.exec_module(module)

                # starting the module application
                # TODO consider ssl (or use global ssl certs from platform?)
                # TODO maybe wrap in try/except to suggest succes to user (for now just returns True)
                module_config = get_config_path(module_to_start)
                module.apply_config(module_config)   # function implemented by module
                module_app = module.make_app()  # function implemented by module

                module_server = tornado.httpserver.HTTPServer(module_app, no_keep_alive=True)  # need no-keep-alive to be able to stop server
                servers[module_to_start] = module_server
                port = determine_free_port()
                module_server.listen(port)
                self.write({'type': 'starting_response',
                            'module': module_to_start,
                            'success': True,
                            'port': port})
            else:
                print("module already running, starting denied. stop module first")
                self.write({'type': 'starting_response',
                            'module': module_to_start,
                            'success': False,
                            'reason': 'already_running'})
        elif slug == "stop":
            module_to_stop = self.get_argument("module_name", None)
            shutdown_module(module_to_stop)


def shutdown_module(module_name):
    """
    Stop a module, i.e. call the stop_signal function of the module and stop the module's http server.
    this function is not supposed to be called directly, it is called through the API

    :param module_name: the module to stop

    """

    if module_name in servers:
        if module_name in sys.modules:
            # TODO check (maybe with hasattr) if the module has this function
            sys.modules[module_name].stop_signal()  # call the stop function of the module to indicate stopping
        server = servers[module_name]
        server.stop()  # stop the corresponding server, note: after calling stop, requests in progress will still continue
        del servers[module_name]


def make_app():
    """
    Build the tornado Application

    :returns: the tornado application
    :rtype: tornado.web.Application

    """

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/modules/([a-zA-Z\-0-9\.:,_]+)", ModuleHandler),
        (r"/configs/([a-zA-Z\-0-9\.:,_]+)", ConfigHandler),
        (r"/execution/([a-zA-Z\-0-9\.:,_]+)", ExecutionHandler),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css/"})
    ])


if __name__ == '__main__':
    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    servers['platform'] = server
    server.listen(8888)
    tornado.ioloop.IOLoop.current().start()
