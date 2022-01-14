from abc import ABCMeta

import bcrypt
import tornado.escape
import tornado.ioloop
import tornado.web

from db_access import execute, is_admin, query, queryone
from handlers.base_handler import BaseHandler
from handlers.module_communication_handlers import WebsocketHandler
from logger_factory import log_access
from token_cache import token_cache


class AccountDeleteHandler(BaseHandler, metaclass=ABCMeta):
    """
    Fully delete the account and all information

    """

    @log_access
    async def delete(self):
        """
        DELETE request of /delete_account
            delete the currently logged in account. To confirm this action was taken by the correct user the password
            needs to validate
            query param: password

        success:
            204
        error:
            400 -> missing query parameter
            401 -> password validation failed
            401 -> no token

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

                # message all modules that this account was deleted, it is their responsibility to treat it accordingly
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


class RoleHandler(BaseHandler, metaclass=ABCMeta):
    """
    Read and update options for user roles

    """

    @log_access
    async def get(self):
        """
        GET request of /roles
            request the role of the currently logged in user

        success:
            200, {"type": "permission_response", "role": <str>}
        error:
            401 -> no token

        """

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

    @log_access
    async def post(self):
        """
        POST request of /roles
            change the role of a certain user with help of the query parameters. only an account with the "admin" role
            is able to perform this action.

            query param: user_name
            query param: role

        success:
            200
        error:
            401 -> no token
            401 -> user not admin

        """

        if self.current_user:
            if await is_admin(self.current_user["name"]):
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


class UserHandler(BaseHandler, metaclass=ABCMeta):
    """
    endpoint to request user information

    """

    @log_access
    async def get(self):
        """
        GET request of /users
            request user information of all users (id, name, email, role).
            only an account with the "admin" role can perform this action

        success:
            200, {"status": 200, "success": True, "user_list": [<user_obj>]}
        error:
            401 -> no token
            401 -> user not admin

        """

        if self.current_user:
            if await is_admin(self.current_user["name"]):
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
