from abc import ABCMeta
import os

import CONSTANTS
from handlers.base_handler import BaseHandler
from logger_factory import log_access

# TODO since we also send this information via the websocket we might not even need this handler


class TemplateHandler(BaseHandler, metaclass=ABCMeta):

    @log_access
    def get(self):

        if self.current_user:
            template_name = self.get_argument("template")

            if os.path.isdir(CONSTANTS.TEMPLATES_DIR):
                if os.path.isfile(CONSTANTS.TEMPLATES_DIR + template_name):
                    with open(CONSTANTS.TEMPLATES_DIR + template_name, "r") as fp:
                        template_str = fp.read()

                        self.write({"template": template_str})
                        # TODO error handling: dir not found, file not found, not logged in, ...

