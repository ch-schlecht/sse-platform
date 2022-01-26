from abc import ABCMeta
import json

from keycloak import KeycloakGetError
import tornado.web

from db_access import queryone
import global_vars
from token_cache import token_cache


class BaseHandler(tornado.web.RequestHandler, metaclass=ABCMeta):
    """
    BaseHandler to be inherited from by the other Handlers
    Implements functionality to authenticate the user based on its token

    """
    # use prepare instead of get_current_user because prepare can be async
    async def prepare(self):
        """
        """
        token = self.get_secure_cookie("access_token")
        if token is not None:
            token = json.loads(token)
        else:
            self.redirect("/login")

        try:
            # try to refresh the token and fetch user info. this will fail if there is no valid session
            token = global_vars.keycloak.refresh_token(token['refresh_token'])

            userinfo = global_vars.keycloak.userinfo(token['access_token'])
            # if token is still valid --> successfull authentication --> we set the current_user
            if userinfo:
                result = await queryone("SELECT id FROM users WHERE email = %s", userinfo["email"])
                self.current_user = result["id"]
                print(self.current_user)
                self.userinfo = userinfo
                self._access_token = token
        except KeycloakGetError as e:
            # something wrong with request
            # decode error message
            decoded = json.loads(e.response_body.decode())
            # no active session means user is not logged in --> redirect him straight to login
            if decoded["error"] == "invalid_grant" and decoded["error_description"] == "Session not active":
                self.current_user = None
                self._access_token = None
                self.redirect("/login")

    def get(self):
        self.redirect("/main")
