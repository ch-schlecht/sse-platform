from abc import ABCMeta
import json

from keycloak import KeycloakGetError
from keycloak.exceptions import KeycloakError
from tornado.options import options
import tornado.web

import global_vars


class BaseHandler(tornado.web.RequestHandler, metaclass=ABCMeta):
    """
    BaseHandler to be inherited from by the other Handlers
    Implements functionality to authenticate the user based on its token

    """

    # use prepare instead of get_current_user because prepare can be async
    async def prepare(self):
        """
        validate the user's session against the keycloak server
        if the token is no longer valid, redirect to login page
        """

        # set user for test environment to bypass authentication in the handlers
        if options.test:
            self.current_userinfo = {'sub': 'aaaaaaaa-bbbb-0000-cccc-dddddddddddd',
                                     'resource_access': {'test': {'roles': ['admin']}},
                                     'email_verified': True, 'name': 'Test Admin',
                                     'preferred_username': 'test_admin',
                                     'given_name': 'Test', 'family_name': 'Admin',
                                     'email': 'test_admin@mail.de'}
            self.current_user = self.current_userinfo["sub"]
            self._access_token = {'access_token': 'abcdefg', 'expires_in': 3600,
                                  'refresh_expires_in': 3600, 'refresh_token': 'hijklmn',
                                  'token_type': 'Bearer', 'not-before-policy': 0,
                                  'session_state': 'abcdefgh-1234-ijkl-56m7-nopqrstuv890',
                                  'scope': 'email profile'}
            return

        # grab token from cookie, if there is none, redirect to login
        token = self.get_secure_cookie("access_token")
        if token is not None:
            token = json.loads(token)
        else:
            self.redirect("/login")
            return

        try:
            # try to refresh the token and fetch user info. this will fail if there is no valid session
            token = global_vars.keycloak.refresh_token(token['refresh_token'])
            userinfo = global_vars.keycloak.introspect(token['access_token'])
            # if token is still valid --> successfull authentication --> we set the current_user
            if userinfo:
                # set current_user as user id for legacy reasons, TODO might be able to get rid of that
                self.current_user = userinfo["sub"]
                self.current_userinfo = userinfo
                self._access_token = token
        except KeycloakGetError as e:
            print(e)
            # something wrong with request
            # decode error message
            decoded = json.loads(e.response_body.decode())

            # no active session means user is not logged in --> redirect him straight to login
            if decoded["error"] == "invalid_grant" and decoded["error_description"] == "Session not active":
                self.current_user = None
                self.current_userinfo = None
                self._access_token = None
                self.redirect("/login")
        except KeycloakError as e:
            print(e)
            self.current_user = None
            self.current_userinfo = None
            self._access_token = None
            self.redirect("/login")

    def is_current_user_admin(self):
        if not self.current_userinfo:
            return False
        if "admin" in self.current_userinfo["resource_access"][global_vars.keycloak_client_id]["roles"]:
            return True
        else:
            return False

    def get(self):
        self.redirect("/main")
