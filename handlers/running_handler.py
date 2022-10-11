from abc import ABCMeta

import global_vars
from handlers.base_handler import BaseHandler
from logger_factory import log_access


class RunningHandler(BaseHandler, metaclass=ABCMeta):
    """
    Endpoint to see Running Modules

    """

    @log_access
    async def get(self):
        """
        GET request of /execution/running

        success:
            200, {"running_modules": {"<module_name>": {"port":"<int>"}}, {...} }
        error:
            401 -> no token

        """

        if self.current_user:
            data = {}
            for module_name in global_vars.servers.keys():
                data[module_name] = {"port": global_vars.servers[module_name]["port"]}
            self.set_status(200)
            self.write({"running_modules": data})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})
