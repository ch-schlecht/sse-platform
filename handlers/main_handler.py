from abc import ABCMeta

from handlers.base_handler import BaseHandler
from logger_factory import log_access


class MainHandler(BaseHandler, metaclass=ABCMeta):
    """
    Serves the Frontend

    """

    @log_access
    async def get(self):
        """
        GET request for the main page. If the user is an admin, admin.html is rendered, user.html otherwise
        If there is no logged in user, you will be redirected to the login page

        success:
            200, html
        error:
            n/a
        """

        if self.current_user:
            if self.is_current_user_admin():
                await self.render("../html/admin.html")
            else:
                await self.render("../html/user.html")
        else:
            self.redirect("/login")
