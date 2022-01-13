import sys
import asyncio
if sys.platform == 'win32':  # windows bug workaround, see https://github.com/tornadoweb/tornado/issues/2608 for details
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import argparse
import json
import ssl

from keycloak import KeycloakOpenID
import tornado.ioloop
import tornado.locks
import tornado.httpserver
import tornado.web

import CONSTANTS
import global_vars
from db_access import initialize_db
from handlers.authentification_handlers import ForgotPasswordHandler, GoogleLoginHandler, LoginHandler, LoginCallbackHandler, LogoutHandler, \
    PasswordHandler, RegisterHandler
from handlers.base_handler import BaseHandler
from handlers.main_handler import MainHandler
from handlers.module_communication_handlers import WebsocketHandler
from handlers.running_handler import RunningHandler
from handlers.template_handler import TemplateHandler
from handlers.user_management_handlers import AccountDeleteHandler, RoleHandler, UserHandler
from handlers.util_handlers import RoutingHandler
from handlers.enmeshed_handler import EnmeshedSyncHandler, EnmeshedInformationHandler
from logger_factory import get_logger

logger = get_logger(__name__)

with open("client_secret.txt", "r") as fp:
    client_secret = fp.read()

global_vars.keycloak = KeycloakOpenID("https://skm.sc.uni-leipzig.de/auth/", realm_name="kavaq", client_id="test",
                              client_secret_key=client_secret)

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    any unhandled exceptions get passed to our logger, so that we also have complete stacktraces of exceptions in the logfile
    """

    if issubclass(exc_type, KeyboardInterrupt):  # ignore KeyboardInterrupt exception, they always appear when stopping the script with CTRL + C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception  # register our exception handler to the exception hook


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
        (r"/register", RegisterHandler),
        (r"/login", LoginHandler),
        (r"/login/callback", LoginCallbackHandler),
        (r"/google_signin", GoogleLoginHandler),
        (r"/logout", LogoutHandler),
        (r"/password/\b(change|forgot)\b", PasswordHandler),
        (r"/delete_account", AccountDeleteHandler),
        (r"/forgot_password", ForgotPasswordHandler),
        (r"/roles", RoleHandler),
        (r"/routing", RoutingHandler),
        (r"/template", TemplateHandler),
        (r"/users", UserHandler),
        (r"/websocket", WebsocketHandler),
        (r"/sync", EnmeshedSyncHandler),
        (r"/enmeshed", EnmeshedInformationHandler),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css/"}),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "./img/"}),
        (r"/html/(.*)", tornado.web.StaticFileHandler, {"path": "./html/"}),
        (r"/javascripts/(.*)", tornado.web.StaticFileHandler, {"path": "./javascripts/"})
    ], cookie_secret=cookie_secret)


async def main() -> None:
    """
    the main function.
        1. parse command line arguments
        2. load ssl context (needed for https)
        3. init the database (connect, create tables if necessary)
        4. start the server

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, help="path to config file")
    parser.add_argument("--create_admin", help="create an admin account (with credentials from config)", action="store_true")
    args = parser.parse_args()

    # deal with config properties
    if args.config:
        with open(args.config) as json_file:
            config = json.load(json_file)

        if args.config != CONSTANTS.CONFIG_PATH:
            CONSTANTS.CONFIG_PATH = args.config

        if "routing" in config:
            global_vars.routing = config["routing"]

    else:
        logger.critical('config not supplied or an error occured when reading the file')
        sys.exit(-1)

    # init database
    await initialize_db(args.create_admin)

    app = make_app(config["cookie_secret"])
    server = tornado.httpserver.HTTPServer(app)
    global_vars.servers['platform'] = {"port": CONSTANTS.PORT}
    server.listen(CONSTANTS.PORT)

    logger.info("Platform started on port: " + str(CONSTANTS.PORT))

    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()


if __name__ == '__main__':
    tornado.ioloop.IOLoop.current().run_sync(main)
