import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import tornado.ioloop
import tornado.escape
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.locks
import bcrypt
import json
import argparse
import ssl
import CONSTANTS
import os
import signing
import nacl.signing
import nacl.encoding
import nacl.exceptions
from github_access import list_modules
from db_access import initialize_db, queryone, query, user_exists, NoResultError, is_admin, execute, get_role
from token_cache import token_cache
from base64 import b64encode
import uuid
import smtplib
from email.message import EmailMessage

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
        Checks for the presence of the access token.
        First the "access_token" cookie is checked. If it is not present there,
        the Authorization Header is checked.
        If it is present anywhere in those two places and can be associated with a user account, self.current_user
        will be overridden to the user id, meaning the user is authenticated.
        If not present or not associated with a user, self.current_user will be
        set to None, meaning no authentication is granted.

        If the server was started with the --dev flag (for dev-mode), self.current_user will be automatically set (-1 as indicator for dev).
        This means no authentication is needed in dev mode.
        """

        if dev_mode is False:
            token = self.get_secure_cookie("access_token")
            if token is not None:
                token = token.decode("utf-8")  # need to to decoding separate because of possible None value
            else:  # cookie not set, try to auth with authorization header
                if "Authorization" in self.request.headers:
                    token = self.request.headers["Authorization"]
            self._access_token = token

            cached_user = token_cache().get(token)
            if cached_user is not None:
                self.current_user = cached_user["user_id"]
            else:
                self.current_user = None
        else:
            self.current_user = -1

    def get(self):
        self.redirect("/main")


class MainHandler(BaseHandler):
    """
    Serves the Frontend

    """

    async def get(self):
        """
        GET request for the index.html page

        """
        if self.current_user:
            if await is_admin(self.current_user):
                self.render("admin.html")
            else:
                self.render("user.html")
        else:
            self.redirect("/login")


class ModuleHandler(BaseHandler):
    """
    Handles module architecture

    """

    async def get(self, slug):
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
            if modules:
                self.write({'type': 'list_available_modules',
                            'modules': modules,
                            'success': True})
            else:
                self.write({'type': 'list_available_modules',
                            'success': False,
                            'reason': 'no_github_api_connection'})


class ExecutionHandler(BaseHandler):
    """
    handles execution and stopping of modules

    """

    async def get(self, slug):
        """
        GET request of /execution/running
        """

        if self.current_user:
            if slug == "running":
                data = {}
                for module_name in servers.keys():
                    data[module_name] = {"port": servers[module_name]["port"]}
                self.set_status(200)
                self.write({"running_modules": data})
                # show running things, and its config
                #for i in server_services:
                #    print(i)

                #    data['server_services'] = server_services

                #self.render('templates/exe.html', data=data)

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
        self.render("index.html")

    async def post(self):
        """
        POST request of /login

        query param: `email`
        query param: `nickname`
        query param: `password`

        """
        try:
            email = self.get_argument("email", "")
            nickname = self.get_argument("nickname", "")
            password = self.get_argument("password")
            user = await queryone("SELECT * FROM users WHERE email = %s OR name = %s", email, nickname)
        except tornado.web.MissingArgumentError: # either email/nickname or password have not been sent in the request
            self.set_status(400)
            self.write({"status": 400,
                        "reason": "missing_query_parameter",
                        "redirect_suggestions": ["/login", "/register"]})
            self.flush()
            self.finish()
            return
        except NoResultError:  # user does not exist
            self.set_status(409)
            self.write({"status": 409,
                        "reason": "user_not_found",
                        "redirect_suggestions": ["/login", "/register"]})
            self.flush()
            self.finish()
            return

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

            role = await get_role(user["id"])
            token_cache().insert(access_token, user['id'], user["name"], user["email"], role)

            self.set_secure_cookie("access_token", access_token)

            # broadcast user login to modules
            data = {"type": "user_login",
                    "username": user["name"],
                    "email": user["email"],
                    "id": user["id"],
                    "role": role,
                    "access_token": access_token}
            tornado.ioloop.IOLoop.current().add_callback(WebsocketHandler.broadcast_message, data)

            self.set_status(200)
            self.write({"status": 200,
                        "success": True,
                        "access_token": access_token})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "success": False,
                        "reason": "password_validation_failed",
                        "redirect_suggestions": ["/login", "/register"]})


class LogoutHandler(BaseHandler):

    def get(self):
        pass

    def post(self):
        # simply remove token from the cache and clear the cookie --> user needs to login again to proceed
        token_cache().remove(self._access_token)

        data = {"type": "user_logout",
                "access_token": self._access_token}
        tornado.ioloop.IOLoop.current().add_callback(WebsocketHandler.broadcast_message, data)

        self.clear_cookie("access_token")

        self.set_status(200)
        self.write({"status": 200,
                    "success": True,
                    "redirect_suggestions": ["/login"]})


class RegisterHandler(BaseHandler):
    """
    Register an account towards the API
    """

    def get(self):
        self.render("index.html")

    async def post(self):
        """
        POST request of /register

        query param: `email`
        query param: `nickname`
        query param: `password`

        """

        try:
            email = self.get_argument("email")
            nickname = self.get_argument("nickname")
            unhashed_password = self.get_argument("password")
        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"status": 400,
                        "reason": "missing_query_parameter",
                        "redirect_suggestions": ["/login", "/register"]})
            return

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
            self.finish()
            return
        else:
            # save user, generate token, store and return it
            result = await queryone("INSERT INTO users (email, name, hashed_password, role) \
                            VALUES (%s, %s, %s, %s) RETURNING id",
                            email, nickname, tornado.escape.to_unicode(hashed_password), "guest")
            user_id = result['id']

            access_token = b64encode(os.urandom(CONSTANTS.TOKEN_SIZE)).decode("utf-8")

            role = await get_role(user_id)
            token_cache().insert(access_token, user_id, nickname, email, role)

            self.set_secure_cookie("access_token", access_token)

            # broadcast user login to modules
            data = {"type": "user_login",
                    "username": nickname,
                    "email": email,
                    "id": user_id,
                    "role": role,
                    "access_token": access_token}
            tornado.ioloop.IOLoop.current().add_callback(WebsocketHandler.broadcast_message, data)

            self.set_status(200)
            self.write({"status": 200,
                        "success": True,
                        "access_token": access_token})


class PasswordHandler(BaseHandler):

    def get(self, slug):
        """
        GET request of /password/change

            render the page to change your password
        """

        if self.current_user:
            if slug == "change":
                self.render("change_password.html")
        else:
            self.redirect("/login")

    async def post(self, slug):
        """
        POST request of /password/change

            query param: "old_password"
            query param: "new_password

        or

        POST request of /password/forgot

            query param: "email"
        """
        if slug == "change":
            if self.current_user:
                try:
                    old_password = self.get_argument("old_password")
                    new_password = self.get_argument("new_password")
                    user = await queryone("SELECT * FROM users WHERE id = %s", self.current_user)
                except tornado.web.MissingArgumentError:  # either old or new password have not been sent in the request
                    self.set_status(400)
                    self.write({"status": 400,
                                "reason": "missing_query_parameter",
                                "redirect_suggestions": ["/login", "/register"]})
                    self.flush()
                    self.finish()
                    return

                # check if old password matches
                password_validated = await tornado.ioloop.IOLoop.current().run_in_executor(
                    None,
                    bcrypt.checkpw,
                    tornado.escape.utf8(old_password),
                    tornado.escape.utf8(user['hashed_password'])
                )

                if password_validated:
                    new_hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
                        None,
                        bcrypt.hashpw,
                        tornado.escape.utf8(new_password),
                        bcrypt.gensalt(),
                    )

                    # save the new password in the db
                    await execute("UPDATE users SET hashed_password = %s WHERE id = %s", tornado.escape.to_unicode(new_hashed_password), user["id"])

                    # invalidate token and cache entry --> force relogin
                    token_cache().remove(self._access_token)
                    self.clear_cookie("access_token")

                    self.set_status(200)
                    self.write({"status": 200,
                                "success": True,
                                "redirect": "/login"})
                else:
                    self.set_status(400)
                    self.write({"status": 400,
                                "reason": "old_password_not_valid",
                                "redirect_suggestions": ["/login"]})

            else:
                self.set_status(401)
                self.write({"status": 401,
                            "reason": "no_token",
                            "redirect_suggestions": ["/login"]})

        elif slug == "forgot":
            try:
                email = self.get_argument("email")
            except tornado.web.MissingArgumentError:
                self.set_status(400)
                self.write({"status": 400,
                            "reason": "missing_query_parameter",
                            "redirect_suggestions": ["/login", "/register"]})
                self.flush()
                self.finish()
                return

            identifier = str(uuid.uuid4())

            # either set up own smtp server on this host, or use another one an create a secure connection to it
            # for now use localhost with a debugging smtp server just for development
            # debugging server: python3 -m smtpd -c DebuggingServer -n localhost:1025
            # TODO use tls in production
            with smtplib.SMTP("localhost", 1025) as server:
                msg = EmailMessage()
                msg["Subject"] = "Your Link to reset your password"
                msg["From"] = "no_reply@sse-platform.net"
                msg["To"] = email

                msg.set_payload("Dear user, this is your link to reset your password: "
                                "https://localhost:8888/forgot_password?phrase=" + identifier)  # todo generate host and port from config/constants
                server.send_message(msg)

                await execute("INSERT INTO password_reset(phrase, email) VALUES (%s, %s)", identifier, email)

            self.set_status(204)


class ForgotPasswordHandler(BaseHandler):
    def get(self):
        self.render("forgot_password.html")

    async def post(self):
        try:
            phrase = self.get_argument("phrase")
            new_pw = self.get_argument("new_password")
        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"status": 400,
                        "reason": "missing_query_parameter",
                        "redirect_suggestions": ["/login", "/register"]})
            self.flush()
            self.finish()
            return

        try:
            record = await queryone("SELECT * FROM password_reset WHERE phrase = %s", phrase)
        except NoResultError:
            self.set_status(400)
            self.write({"status": 400,
                        "reason": "phrase_not_valid",
                        "redirect_suggestions": ["/login", "/register"]})
            self.flush()
            self.finish()
            return

        user = await queryone("SELECT * FROM users WHERE email=%s", record["email"])

        new_hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(new_pw),
            bcrypt.gensalt(),
        )
        # save the new password in the db
        await execute("UPDATE users SET hashed_password = %s WHERE id = %s",
                      tornado.escape.to_unicode(new_hashed_password), user["id"])

        await execute("DELETE FROM password_reset WHERE phrase = %s", phrase)

        # TODO error handling

        self.set_status(200)
        self.write({"status": 200,
                    "success": True,
                    "redirect": "/login"})









class AccountDeleteHandler(BaseHandler):
    async def delete(self):
        """
        DELETE /account
        """

        if self.current_user:
            try:
                password = self.get_argument("password")
            except tornado.web.MissingArgumentError:  # password has not been sent in the request
                self.set_status(400)
                self.write({"status": 400,
                            "reason": "missing_query_parameter",
                            "redirect_suggestions": ["/login", "/register"]})
                self.flush()
                self.finish()
                return
            user = await queryone("SELECT * FROM users WHERE id = %s", self.current_user)

            # check password validation
            password_validated = await tornado.ioloop.IOLoop.current().run_in_executor(
                None,
                bcrypt.checkpw,
                tornado.escape.utf8(password),
                tornado.escape.utf8(user['hashed_password'])
            )

            if password_validated:
                await execute("DELETE FROM users WHERE id = %s", self.current_user)  # delete user data
                # invalidate token and cache entry --> force logout
                token_cache().remove(self._access_token)
                self.clear_cookie("access_token")

                # message all modules that this account was deleted
                data = {"type": "user_delete",
                        "userid": self.current_user,
                        "access_token": self._access_token}
                tornado.ioloop.IOLoop.current().add_callback(WebsocketHandler.broadcast_message, data)

                self.set_status(204)
            else:
                self.set_status(401)
                self.write({"status": 401,
                            "success": False,
                            "reason": "password_validation_failed"})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})


class RoleHandler(BaseHandler):

    async def get(self):
        if self.current_user:
            result = await queryone("SELECT role FROM users WHERE id=%s", self.current_user)
            self.set_status(200)
            self.write({"type": "permission_response",
                        "role": result["role"]})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})

    async def post(self):
        if self.current_user:
            if await is_admin(self.current_user):
                user_name = self.get_argument("user_name")
                role = self.get_argument("role")
                await execute("UPDATE users SET role = %s WHERE name = %s", role, user_name)

                self.set_status(200)
                self.write({"status": 200,
                            "success": True})
            else:
                self.set_status(401)
                self.write({"status": 401,
                            "reason": "user_not_admin",
                            "redirect_suggestions": ["/login"]})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})


class UserHandler(BaseHandler):

    async def get(self):
        if self.current_user:
            if await is_admin(self.current_user):
                user_list = [user for user in await query("SELECT id, name, email, role FROM users")]
                self.set_status(200)
                self.write({"status": 200,
                            "success": True,
                            "user_list": user_list})
            else:
                self.set_status(401)
                self.write({"status": 401,
                            "reason": "user_not_admin",
                            "redirect_suggestions": ["/login"]})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})


class WebsocketHandler(tornado.websocket.WebSocketHandler):

    connections = set()

    def verify_msg(self, message):
        message = tornado.escape.json_decode(message)
        with open("verify_keys.json", "r") as fp:
            verify_keys = json.load(fp)

        origin = message["origin"]
        if origin in verify_keys:
            verify_key_b64 = verify_keys[origin].encode("utf8")
            verify_key = nacl.signing.VerifyKey(verify_key_b64, encoder=nacl.encoding.Base64Encoder)
            try:
                verified = verify_key.verify(message["signed_msg"], encoder=nacl.encoding.Base64Encoder)
                original_message = tornado.escape.json_decode(verified.decode("utf8"))
                if original_message["origin"] == message["origin"]:
                    return original_message
            except nacl.exceptions.BadSignatureError:
                print("Signature validation failed")
                return None

    def sign(self, message):
        pass

    def open(self):
        print("client connected")
        msg = tornado.escape.json_decode(self.request.body)
        self.module_name = msg["module"]
        self.connections.add(self)

    async def on_message(self, message):
        json_message = self.verify_msg(message)
        print("got message:")
        print(json_message)
        if json_message is None:
            self.write_message({"type": "signature_verification_error"})
            return

        if json_message["type"] == "module_start":
            module_name = json_message["module_name"]
            servers[module_name] = {"port": json_message["port"]}
            self.write_message({"type": "module_start_response",
                                "status": "recognized",
                                "resolve_id": json_message["resolve_id"]})

        elif json_message["type"] == "user_logout":
            token = json_message["access_token"]
            token_cache().remove(token)
            self.write_message({"type":"user_logout_response",
                                "success": True,
                                "resolve_id": json_message["resolve_id"]})

        elif json_message['type'] == "get_user":
            username = json_message['username']
            user = await queryone("SELECT id, email, name AS username, role FROM users WHERE name = %s", username)
            self.write_message({"type": "get_user_response",
                                "user": user,
                                "resolve_id": json_message['resolve_id']})

        elif json_message['type'] == "get_user_list":
            users = await query("SELECT id, email, name AS username, role FROM users")
            ret_format = {}
            for user in users:
                ret_format[user["username"]] = user
            self.write_message({"type": "get_user_list_response",
                                "users": ret_format,
                                "resolve_id": json_message['resolve_id']})

        elif json_message["type"] == "token_validation":
            validated_user = token_cache().get(json_message["access_token"])
            if validated_user is not None:
                self.write_message({"type": "token_validation_response",
                                    "success": True,
                                    "user": {
                                        "username": validated_user["username"],
                                        "email": validated_user["email"],
                                        "user_id": validated_user["user_id"],
                                        "role": validated_user["role"],
                                        "expires": str(validated_user["expires"])
                                    },
                                    "resolve_id": json_message["resolve_id"]})
            else:
                self.write_message({"type": "token_validation_response",
                                    "success": False,
                                    "resolve_id": json_message["resolve_id"]})

        elif json_message["type"] == "check_permission":
            username = json_message["username"]
            result = await queryone("SELECT role FROM users WHERE name = %s", username)
            self.write_message({"type": "check_permission_response",
                                "username": username,
                                "role": result["role"],
                                "resolve_id": json_message["resolve_id"]})

    def on_close(self):
        print("Client disconnected: " + self.module_name)
        del servers[self.module_name]
        self.connections.remove(self)

    @classmethod
    def broadcast_message(cls, message):
        for client in cls.connections:
            client.write_message(message)


def make_app(dev_mode_arg, cookie_secret):
    """
    Build the tornado Application

    :returns: the tornado application
    :rtype: tornado.web.Application

    """
    if dev_mode_arg:
        global dev_mode
        dev_mode = True

    return tornado.web.Application([
        (r"/", BaseHandler),
        (r"/main", MainHandler),
        (r"/modules/([a-zA-Z\-0-9\.:,_]+)", ModuleHandler),
        (r"/execution/([a-zA-Z\-0-9\.:,_]+)", ExecutionHandler),
        (r"/register", RegisterHandler),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/password/\b(change|forgot)\b", PasswordHandler),
        (r"/delete_account", AccountDeleteHandler),
        (r"/forgot_password", ForgotPasswordHandler),
        (r"/roles", RoleHandler),
        (r"/users", UserHandler),
        (r"/websocket", WebsocketHandler),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css/"}),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "./img/"}),
        (r"/html/(.*)", tornado.web.StaticFileHandler, {"path": "./html/"}),
        (r"/javascripts/(.*)", tornado.web.StaticFileHandler, {"path": "./javascripts/"})
    ], cookie_secret=cookie_secret)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, help="path to config file")
    parser.add_argument("--dev", help="run in dev mode (no auth needed)", action="store_true")
    parser.add_argument("--create_admin", help="create an admin account (with credentials from config)", action="store_true")
    args = parser.parse_args()

    ssl_ctx = None

    # deal with config properties
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

    # init database
    await initialize_db(args.create_admin)

    app = make_app(args.dev, config["cookie_secret"])
    server = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx)
    servers['platform'] = {"port": CONSTANTS.PORT}
    server_services['platform'] = {}
    server.listen(CONSTANTS.PORT)

    print("Platform started on port: " + str(CONSTANTS.PORT))

    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()


if __name__ == '__main__':
    tornado.ioloop.IOLoop.current().run_sync(main)
