import sys
import asyncio

if sys.platform == 'win32':  # windows bug workaround, see https://github.com/tornadoweb/tornado/issues/2608 for details
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import json
from pprint import pprint

from keycloak import KeycloakOpenID, KeycloakAdmin
import tornado.ioloop
import tornado.locks
import tornado.httpserver
from tornado.options import define, options
import tornado.web

import global_vars
from handlers.authentification_handlers import LoginHandler, LoginCallbackHandler, LogoutHandler
from handlers.base_handler import BaseHandler
from handlers.main_handler import MainHandler
from handlers.module_communication_handlers import WebsocketHandler
from handlers.running_handler import RunningHandler
from handlers.user_management_handlers import AccountDeleteHandler, RoleHandler, UserHandler
from handlers.util_handlers import HealthCheckHandler, RoutingHandler
from logger_factory import get_logger

logger = get_logger(__name__)

define("config", default="config.json", type=str,
       help="path to config file, defaults to config.json")
define("test", default=False, type=bool,
       help="start application in test mode (bypass authentication)")


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    any unhandled exceptions get passed to our logger, so that we also have complete stacktraces of exceptions in the logfile
    """

    # ignore KeyboardInterrupt exception, they always appear when stopping the script with CTRL + C
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(
        exc_type, exc_value, exc_traceback))


# register our exception handler to the exception hook
sys.excepthook = handle_exception


def make_app(cookie_secret: str) -> tornado.web.Application:
    """
    Build the tornado Application

    :param cookie_secret: random string that is used for secure cookies. The platform and all modules need to use the same cookie_secret

    :returns: the tornado application

    """

    return tornado.web.Application([
        (r"/", BaseHandler),
        (r"/main", MainHandler),
        (r"/execution/running", RunningHandler),
        (r"/login", LoginHandler),
        (r"/login/callback", LoginCallbackHandler),
        (r"/logout", LogoutHandler),
        (r"/delete_account", AccountDeleteHandler),
        (r"/roles", RoleHandler),
        (r"/routing", RoutingHandler),
        (r"/users", UserHandler),
        (r"/health", HealthCheckHandler),
        (r"/websocket", WebsocketHandler),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css/"}),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "./img/"}),
        (r"/html/(.*)", tornado.web.StaticFileHandler, {"path": "./html/"}),
        (r"/javascripts/(.*)", tornado.web.StaticFileHandler,
         {"path": "./javascripts/"})
    ], cookie_secret=cookie_secret)


async def main() -> None:
    """
    the main function.
        1. parse command line arguments
        2. build app & http server
        3. start and run until stopped

    """
    tornado.options.parse_command_line()

    # deal with config properties
    with open(options.config) as json_file:
        config = json.load(json_file)

    global_vars.port = int(config["port"])
    global_vars.keycloak = KeycloakOpenID(config["keycloak_base_url"], realm_name=config["keycloak_realm"], client_id=config["keycloak_client_id"],
                                          client_secret_key=config["keycloak_client_secret"])
    global_vars.keycloak_admin = KeycloakAdmin(config["keycloak_base_url"], realm_name=config["keycloak_realm"], username=config["keycloak_admin_username"],
                                               password=config["keycloak_admin_password"], verify=True, auto_refresh_token=['get', 'put', 'post', 'delete'])
    global_vars.keycloak_callback_url = config["keycloak_callback_url"]
    global_vars.config_path = options.config
    global_vars.domain = config["domain"]
    global_vars.keycloak_client_id = config["keycloak_client_id"]
    global_vars.templates_dir = config["templates_directory"]
    global_vars.cookie_secret = config["cookie_secret"]

    if "routing" in config:
        global_vars.routing = config["routing"]

    app = make_app(global_vars.cookie_secret)
    server = tornado.httpserver.HTTPServer(app)
    global_vars.servers['platform'] = {"port": global_vars.port}
    server.listen(global_vars.port)

    logger.info("Platform started on port: " + str(global_vars.port))

    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()


if __name__ == '__main__':
    tornado.ioloop.IOLoop.current().run_sync(main)
