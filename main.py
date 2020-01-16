import tornado.ioloop
import tornado.web
import tornado.locks
import bcrypt
import importlib
import sys
import json
import argparse
import ssl
import CONSTANTS
import os
from CONSTANTS import MODULE_PACKAGE
from github_access import list_modules, clone
from util import list_installed_modules, remove_module_files, get_config_path, load_config, write_config, \
    determine_free_port
from db_access import initialize_db, queryone, user_exists, NoResultError
from token_cache import token_cache
from base64 import b64encode

servers = {}
server_services = {}
dev_mode = False


class BaseHandler(tornado.web.RequestHandler):
    """
    BaseHandler to be inherited from by the other Handlers
    Implements functionality to authenticate the user based on its token
    """

    # use prepare instead of get_current_user because prepare can be async
    def prepare(self):
        """
        Checks for the access token in the Authorization header.
        If it is present and can be associated with a user account, self.current_user
        will be overridden to the user id, meaning the user is authenticated.
        If not present or not associated with a user, self.current_user will be
        set to None, meaning no authentication is granted.

        If the server was started with the --dev flag (for dev-mode), self.current_user will be automatically set (-1 as indicator for dev).
        This means no authentication is needed in dev mode.
        """

        if dev_mode is False:
            if "Authorization" in self.request.headers:
                token = self.request.headers["Authorization"]
                cached_user = token_cache().get(token)
                if cached_user is not None:
                    self.current_user = cached_user["user_id"]
                else:
                    self.current_user = None
            else:
                self.current_user = None
        else:
            self.current_user = -1  # user_id -1 indicates developer mode


class MainHandler(BaseHandler):
    """
    Serves the Frontend

    """

    def get(self):
        """
        GET request for the index.html page

        """
        if self.current_user:
            self.render("index.html")
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})


class ModuleHandler(BaseHandler):
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
            if self.current_user:
                modules = list_installed_modules()
                self.write({'type': 'list_installed_modules',
                            'installed_modules': modules})
            else:
                self.set_status(401)
                self.write({"status": 401,
                            "reason": "no_token",
                            "redirect_suggestions": ["/login"]})

        elif slug == "download":  # download module given by query param 'name'
            if self.current_user:
                module_to_download = self.get_argument('module_name',
                                                       None)  # TODO handle input of wrong module name (BaseModule?)
                print("Installing Module: " + module_to_download)
                success = clone(module_to_download)  # download module
                self.write({'type': 'installation_response',
                            'module': module_to_download,
                            'success': success})
            else:
                self.set_status(401)
                self.write({"status": 401,
                            "reason": "no_token",
                            "redirect_suggestions": ["/login"]})

        elif slug == "uninstall":  # uninstall module given by query param 'name'
            if self.current_user:
                module_to_uninstall = self.get_argument('module_name', None)

                # check the module is not running, and if, stop it before uninstalling
                if module_to_uninstall in servers:
                    shutdown_module(module_to_uninstall)

                print('Uninstalling Module: ' + module_to_uninstall)
                success = remove_module_files(module_to_uninstall)
                self.write({'type': 'uninstallation_response',
                            'module': module_to_uninstall,
                            'success': success})
            else:
                self.set_status(401)
                self.write({"status": 401,
                            "reason": "no_token",
                            "redirect_suggestions": ["/login"]})


class ConfigHandler(BaseHandler):
    """
    Handles configs of modules

    """

    def get(self, slug):
        """
        GET request of /configs/view
            query param: 'module_name'
                get the config of the module given by module_name

        """
        if self.current_user:
            if slug == "view":
                module = self.get_argument("module_name", None)  # TODO handle input of wrong module name
                config_path = get_config_path(module)
                config = load_config(config_path)
                self.write({'type': 'view_config',
                            'module': module,
                            'config': config})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})

    def post(self, slug):
        """
        POST request of /configs/update
            query param: 'module_name'
            http body: json
                changes the config of the module given by module_name to the json in the http body

        """
        if self.current_user:
            if slug == "update":
                module = self.get_argument("module_name", None)  # TODO handle input of wrong module name
                config_path = get_config_path(module)
                new_config = tornado.escape.json_decode(self.request.body)
                write_config(config_path, new_config)
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})


class ExecutionHandler(BaseHandler):
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
        if self.current_user:
            data = {}
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
                    module.apply_config(module_config)  # function implemented by module
                    module_config_path = get_config_path(module_to_start)
                    with open(module_config_path) as json_file:
                        module_config = json.load(json_file)
                    module.apply_config(module_config)   # function implemented by module
                    module_app = module.make_app()  # function implemented by module

                    module_server = tornado.httpserver.HTTPServer(module_app,
                                                                  no_keep_alive=True)  # need no-keep-alive to be able to stop server
                    port = determine_free_port()

                    servers[module_to_start] = {"server": module_server, "port": port}

                    # set services
                    if hasattr(module, 'get_services') and callable(getattr(module, 'get_services')):
                        ii = module.get_services()
                        server_services[module_to_start] = {"port": port, "service": ii}

                    else:
                        server_services[module_to_start] = {"port": port, "service": {}}

                    module_server.listen(port)
                    self.write({'type': 'starting_response',
                                'module': module_to_start,
                                'success': True,
                                'port': port})
                else:
                    print("module already running, starting denied. stop module first")
                    self.write({'type': 'starting_response',
                                'module': module_to_start,
                                'port': servers[module_to_start]['port'],
                                'success': False,
                                'reason': 'already_running'})
            elif slug == "stop":
                module_to_stop = self.get_argument("module_name", None)
                shutdown_module(module_to_stop)
            elif slug == "running":

                # show running things, and its config
                for i in server_services:
                    print(i)

                    data['server_services'] = server_services

                self.render('templates/exe.html', data=data)

        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})


class CommunicationHandler(tornado.web.RequestHandler):

    def post(self):
        print('getsome_shit')


class LoginHandler(BaseHandler):
    """
    Authenticate a user towards the API
    """

    def get(self):
        pass
        # TODO maybe render a login.html (if it is not a web frontend, it simply shouldnt call get)

    async def post(self):
        """
        POST request of /login

        query param: `email`
        query param: `nickname`
        query param: `password`

        """
        # TODO check for self.current_user, if already set, user is authenticated and can be redirected to MainHandler

        # TODO check if those arguments were set, if not, return 400 bad request
        email = self.get_argument("email", "")
        nickname = self.get_argument("nickname", "")
        password = self.get_argument("password")

        try:
            user = await queryone("SELECT * FROM users WHERE email = %s OR name = %s", email, nickname)
        except NoResultError:  # user does not exist
            self.set_status(409)
            self.write({"status": 409,
                        "reason": "user_not_found",
                        "redirect_suggestions": ["/login", "/register"]})
            self.flush()

        # check passwords match
        password_validated = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.checkpw,
            tornado.escape.utf8(password),
            tornado.escape.utf8(user['hashed_password'])
        )

        if password_validated:
            # generate token, store and return it
            access_token = b64encode(os.urandom(CONSTANTS.TOKEN_SIZE)).decode("utf-8")

            token_cache().insert(access_token, user['id'])

            self.set_status(200)
            self.write({"status": 200,
                        "success": True,
                        "access_token": access_token})
        else:
            self.status(401)
            self.write({"status": 401,
                        "success": False,
                        "reason": "password_validation_failed",
                        "redirect_suggestions": ["/login", "/register"]})


class RegisterHandler(BaseHandler):
    """
    Register an account towards the API
    """

    def get(self):
        self.set_status(501)
        self.write({"status": 501,
                    "reason": "not_yet_implemented"})
        # TODO maybe render a create.html (if it is not a web frontend, it simply shouldnt call get)

    async def post(self):
        """
        POST request of /register

        query param: `email`
        query param: `nickname`
        query param: `password`

        """
        # TODO check if those arguments were set, if not, return 400 bad request
        email = self.get_argument("email")
        nickname = self.get_argument("nickname")
        unhashed_password = self.get_argument("password")

        hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(unhashed_password),
            bcrypt.gensalt(),
        )

        if (await user_exists(nickname)):
            self.set_status(409)
            self.write({"status": 409,
                        "reason": "username_already_exists",
                        "redirect_suggestions": ["/login"]})
            self.flush()
        else:
            # save user, generate token, store and return it
            result = await queryone("INSERT INTO users (email, name, hashed_password, role) \
                            VALUES (%s, %s, %s, %s) RETURNING id",
                            email, nickname, tornado.escape.to_unicode(hashed_password), "user")
            user_id = result['id']

            access_token = b64encode(os.urandom(CONSTANTS.TOKEN_SIZE)).decode("utf-8")

            token_cache().insert(access_token, user_id)

            self.set_status(200)
            self.write({"status": 200,
                        "success": True,
                        "access_token": access_token})


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
        server = servers[module_name]['server']
        server.stop()  # stop the corresponding server, note: after calling stop, requests in progress will still continue
        del servers[module_name]
        del server_services[module_name]


def make_app(dev_mode_arg):
    """
    Build the tornado Application

    :returns: the tornado application
    :rtype: tornado.web.Application

    """
    if dev_mode_arg:
        global dev_mode
        dev_mode = True

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/modules/([a-zA-Z\-0-9\.:,_]+)", ModuleHandler),
        (r"/configs/([a-zA-Z\-0-9\.:,_]+)", ConfigHandler),
        (r"/execution/([a-zA-Z\-0-9\.:,_]+)", ExecutionHandler),
        (r"/register", RegisterHandler),
        (r"/login", LoginHandler),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css/"})
    ])


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, help="path to config file")
    parser.add_argument("--dev", help="run in dev mode (no auth needed)", action="store_true")
    args = parser.parse_args()

    ssl_ctx = None

    if args.config:
        with open(args.config) as json_file:
            config = json.load(json_file)

        if args.config != CONSTANTS.CONFIG_PATH:
            CONSTANTS.CONFIG_PATH = args.config

        if ('ssl_cert' in config) and ('ssl_key' in config):
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(config['ssl_cert'], config['ssl_key'])
        else:
            print('missing ssl_cert or ssl_key in the config or an error occured when reading the file')
            sys.exit(-1)
    else:
        print('config not supplied or an error occured when reading the file')
        sys.exit(-1)

    await initialize_db()

    app = make_app(args.dev)
    server = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx)
    port = 8888
    servers['platform'] = {"server": server, "port": port}
    server_services['platform'] = {}
    server.listen(port)

    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()


if __name__ == '__main__':
    tornado.ioloop.IOLoop.current().run_sync(main)
