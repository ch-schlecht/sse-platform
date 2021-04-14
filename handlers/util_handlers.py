from abc import ABCMeta

import global_vars
from handlers.base_handler import BaseHandler
from logger_factory import log_access


class RoutingHandler(BaseHandler, metaclass=ABCMeta):
    """
    Handles URI Routing

    """

    @log_access
    def get(self):
        """
        GET request of /routing
            send routing information to the frontend to correctly handle href's to modules

        success:
            200, {"module1":"uri1", "module2": "uri2"}
        error:
            401 -> no token

        """

        if self.current_user:
            self.set_status(200)
            self.write(global_vars.routing)
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})
