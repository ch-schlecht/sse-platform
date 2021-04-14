from abc import ABCMeta

import tornado.web

from token_cache import token_cache


class BaseHandler(tornado.web.RequestHandler, metaclass=ABCMeta):
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

        """

        token = self.get_secure_cookie("access_token")
        if token:
            token = token.decode("utf-8")  # need to do decoding separate because of possible None value
        else:  # cookie not set, try to auth with authorization header
            if "Authorization" in self.request.headers:
                token = self.request.headers["Authorization"]
        self._access_token = token

        cached_user = token_cache().get(token)
        if cached_user:
            self.current_user = cached_user["user_id"]
        else:
            self.current_user = None

    def get(self):
        self.redirect("/main")
