from abc import ABCMeta

from db_access import is_admin
from handlers.base_handler import BaseHandler


class MainHandler(BaseHandler, metaclass=ABCMeta):
    """
    Serves the Frontend

    """

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
            if await is_admin(self.current_user):
                await self.render("../html/admin.html")
            else:
                await self.render("../html/user.html")
        else:
            self.redirect("/login")
