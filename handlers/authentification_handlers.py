import json
import os
import smtplib
import uuid
from abc import ABCMeta
from base64 import b64encode
from email.message import EmailMessage

import bcrypt
import tornado.escape
import tornado.ioloop
import tornado.web
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token

import CONSTANTS
from db_access import execute, get_role, insert_google_user_if_not_exists, NoResultError, queryone, user_exists
import global_vars
from handlers.base_handler import BaseHandler
from handlers.module_communication_handlers import WebsocketHandler
from logger_factory import log_access
from token_cache import token_cache


class LoginHandler(tornado.web.RequestHandler, metaclass=ABCMeta):
    """
    Authenticate a user towards the Platform

    """
    @log_access
    def get(self):
        """
        redirect to keycloak

        success:
            200, html
        error:
            n/a

        """
        url = global_vars.keycloak.auth_url("http://localhost:8888/login/callback")
        self.redirect(url)

    @log_access
    async def post(self):
        """
        POST request of /login
            perform the login mechanism using the provided query parameters:

            query param: `email`
            query param: `nickname`
            query param: `password`

        success:
            200, {"status": 200, "success": True, "access_token": "<str>"}
        error:
            400 -> missing query parameter
            401 -> password validation failed
            409 -> user does not exist


        """
        """
        try:
            email = self.get_argument("email", "")
            nickname = self.get_argument("nickname", "")
            password = self.get_argument("password")
            user = await queryone("SELECT * FROM users WHERE email = %s OR name = %s", email, nickname)
        except tornado.web.MissingArgumentError:  # either email/nickname or password have not been sent in the request
            self.set_status(400)
            self.write({"status": 400,
                        "reason": "missing_query_parameter",
                        "redirect_suggestions": ["/login", "/register"]})
            self.finish()
            return
        except NoResultError:  # user does not exist
            self.set_status(409)
            self.write({"status": 409,
                        "reason": "user_not_found",
                        "redirect_suggestions": ["/login", "/register"]})
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

            if CONSTANTS.DOMAIN == "localhost":
                self.set_secure_cookie("access_token", access_token)
            else:
                self.set_secure_cookie("access_token", access_token, domain="." + CONSTANTS.DOMAIN)

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
        """
        pass


class LoginCallbackHandler(tornado.web.RequestHandler, metaclass=ABCMeta):

    async def get(self):
        # keycloak redirects you back here
        # with this code
        code = self.get_argument("code", None)
        if code is None:
            print("error, code None")

        #exchange authorization code for token
        # (redirect_uri has to match the uri in keycloak.auth_url(...) as per openID standard)
        token = global_vars.keycloak.token(code=code, grant_type=["authorization_code"], redirect_uri="http://localhost:8888/login/callback")
        print(token)

        # get user info, (not really necessary here though)
        userinfo = global_vars.keycloak.userinfo(token['access_token'])
        print(userinfo)

        result = await queryone("INSERT INTO users (email, name, role) \
                                             VALUES (%s, %s, %s) ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                                userinfo["email"], userinfo["name"], "guest")
        user_id = result['id']
        print(user_id)

        # dump token dict to str and store it in a secure cookie (BaseHandler will decode it later to validate a user is logged in)
        if CONSTANTS.DOMAIN == "localhost":
            self.set_secure_cookie("access_token", json.dumps(token))
        else:
            self.set_secure_cookie("access_token", json.dumps(token), domain="." + CONSTANTS.DOMAIN)

        self.redirect("/main")


class LogoutHandler(BaseHandler, metaclass=ABCMeta):
    """
    Logout Endpoint
    """

    @log_access
    def post(self):
        """
        POST request of /logout
            perform logout, i.e. clear the token cache entry and delete the cookie

        success:
            200, {"status": 200, "success": True, "redirect_suggestions": ["/login"]}
        error:
            n/a
        """

        if CONSTANTS.DOMAIN == "localhost":
            self.clear_cookie("access_token")
        else:
            self.clear_cookie("access_token", domain="." + CONSTANTS.DOMAIN)

        # perform logout in keycloak
        print(self._access_token)
        global_vars.keycloak.logout(self._access_token["refresh_token"])

        self.set_status(200)
        self.write({"status": 200,
                    "success": True,
                    "redirect_suggestions": ["/login"]})


class RegisterHandler(BaseHandler, metaclass=ABCMeta):
    """
    Register an account towards the Platform
    """

    @log_access
    def get(self):
        """
        GET request /register
            renders the same login page as the login handler

        success:
            200, html
        error:
            n/a

        """
        """
        self.render("../html/index.html")
        """
        pass

    @log_access
    async def post(self):
        """
        POST request of /register
            register a new acount using the query parameters. Successfull registration is also already a login

            query param: `email`
            query param: `nickname`
            query param: `password`

        success:
            200, {"status": 200, "success": True, "access_token": <str>}
        error:
            400 -> missing query parameter
            409 -> user already exists

        """
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

        if await user_exists(nickname):
            self.set_status(409)
            self.write({"status": 409,
                        "reason": "username_already_exists",
                        "redirect_suggestions": ["/login"]})
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

            if CONSTANTS.DOMAIN == "localhost":
                self.set_secure_cookie("access_token", access_token)
            else:
                self.set_secure_cookie("access_token", access_token, domain="." + CONSTANTS.DOMAIN)

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
            """
        pass


class GoogleLoginHandler(BaseHandler, metaclass=ABCMeta):
    """
    Login via OAuth with the Google API

    """

    @log_access
    async def post(self):
        """
        POST request of /google_signin
            perform oauth via google api

            query param: id_token

        success:
            200, {"status": 200, "success": True, "access_token": <str>}
        error:
            400 -> missing query parameter
            401 -> google authentication failed
            401 -> email duplication (email already exists as regular user)

        """
        """
        try:
            token = self.get_argument("id_token")
        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"status": 400,
                        "reason": "missing_query_parameter",
                        "redirect_suggestions": ["/login", "/register"]})
            self.finish()
            return

        # google verification
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), CONSTANTS.CLIENT_ID)
        except GoogleAuthError:
            self.set_status(401)
            self.write({"status": 401,
                        "success": False,
                        "reason": "google_authentication_failed",
                        "redirect_suggestions": ["/login", "/register"]})
            self.finish()
            return

        # generate token, store and return it
        access_token = b64encode(os.urandom(CONSTANTS.TOKEN_SIZE)).decode("utf-8")
        try:
            user = await queryone("SELECT * FROM users WHERE email = %s AND google_user = TRUE", idinfo["email"])
        except NoResultError:
            await insert_google_user_if_not_exists(idinfo["name"], idinfo["email"])
            try:
                user = await queryone("SELECT * FROM users WHERE email = %s AND google_user = TRUE", idinfo["email"])
            except NoResultError:  # if the user was not added it means that his google account email is already registered with us as a normal account, which ist not allowed
                self.set_status(401)
                self.write({"status": 401,
                            "success": False,
                            "reason": "email_duplication",
                            "redirect_suggestions": ["/login", "/register"]})
                self.finish()
                return

        token_cache().insert(access_token, user["id"], user["name"], user["email"], user["role"])

        if CONSTANTS.DOMAIN == "localhost":
            self.set_secure_cookie("access_token", access_token)
        else:
            self.set_secure_cookie("access_token", access_token, domain="." + CONSTANTS.DOMAIN)

        # broadcast user login to modules
        data = {"type": "user_login",
                "username": user["name"],
                "email": user["email"],
                "id": user["id"],
                "role": user["role"],
                "access_token": access_token}
        tornado.ioloop.IOLoop.current().add_callback(WebsocketHandler.broadcast_message, data)

        self.set_status(200)
        self.write({"status": 200,
                    "success": True,
                    "access_token": access_token})
        """
        pass


class PasswordHandler(BaseHandler, metaclass=ABCMeta):
    """
    Endpoints to reset your password or initiate the "forgot password" procedure (send an email to your adress with a link)

    """

    @log_access
    def get(self, slug):
        """
        GET request of /password/change
            render the page to change your password. If there is no logged in user you will be redirected to the login page

        success:
            200, html
        error:
            n/a

        """

        if self.current_user:
            if slug == "change":
                self.render("../html/change_password.html")
        else:
            self.redirect("/login")

    @log_access
    async def post(self, slug):
        """
        POST request of /password/change
            change your password using the query parameters. You will have to relogin afterwards, because your token will
            be invalidated

            query param: "old_password"
            query param: "new_password"

        success:
            200, {"status": 200, "success": True, "redirect": "/login"}
        error:
            400 -> missing query parameter
            400 -> old password not valid
            401 -> no token

        OR

        POST request of /password/forgot
            initiate the forgot password procedure: send an email the adress in the query parameter containing a link
            where you can reset your password.

            query param: "email"

        success:
            204
        error:
            400 -> missing query parameter
        """

        if slug == "change":
            if self.current_user:
                try:
                    old_password = self.get_argument("old_password")
                    new_password = self.get_argument("new_password")
                except tornado.web.MissingArgumentError:  # either old or new password have not been sent in the request
                    self.set_status(400)
                    self.write({"status": 400,
                                "reason": "missing_query_parameter",
                                "redirect_suggestions": ["/login", "/register"]})
                    self.finish()
                    return

                user = await queryone("SELECT * FROM users WHERE id = %s", self.current_user)

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
                    self.clear_cookie("access_token", domain="." + CONSTANTS.DOMAIN)

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

                # store the identifier in the db, knowing that it is active
                await execute("INSERT INTO password_reset(phrase, email) VALUES (%s, %s)", identifier, email)

            self.set_status(204)


class ForgotPasswordHandler(BaseHandler, metaclass=ABCMeta):
    """
    handle the actual forgot password routine, i.e. when the user clicks the link and fills in the form to reset the pw

    """

    @log_access
    def get(self):
        """
        GET request of /forgot_password
            render the landing page

        """

        self.render("../html/forgot_password.html")

    @log_access
    async def post(self):
        """
        POST request of /forgot_password
            reset the users password to a new chosen one. identify that this is the user by the identifier phrase
            in the query parameter. This phrase was sent to him via email. After a successful reset the user has to
            relogin.

            query param: phrase
            query param: new_password

        success:
            200, {"status": 200, "success": True, "redirect": "/login"}
        error:
            400 -> missing query parameter
            400 -> phrase not valid (expired/never generated)

        """

        try:
            phrase = self.get_argument("phrase")
            new_pw = self.get_argument("new_password")
        except tornado.web.MissingArgumentError:
            self.set_status(400)
            self.write({"status": 400,
                        "reason": "missing_query_parameter",
                        "redirect_suggestions": ["/login", "/register"]})
            self.finish()
            return

        try:
            record = await queryone("SELECT * FROM password_reset WHERE phrase = %s", phrase)
        except NoResultError:
            self.set_status(400)
            self.write({"status": 400,
                        "reason": "phrase_not_valid",
                        "redirect_suggestions": ["/login", "/register"]})
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

        # delete the phrase because it was successfully used
        await execute("DELETE FROM password_reset WHERE phrase = %s", phrase)

        # TODO error handling

        self.set_status(200)
        self.write({"status": 200,
                    "success": True,
                    "redirect": "/login"})
