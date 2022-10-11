import functools
import logging
import logging.handlers
from typing import Awaitable, Callable, Optional

import sys
import tornado.web


def get_logger(name: str) -> logging.Logger:
    """
    boilerplate function to create the logger. (DEBUG level to file, INFO level to stdout)
    direction of use:
        logger = get_logger(__name__)
        on top of each script file, log messaging using:
        logger.debug(), .info(), .warning(), ...

    :param name: the name of the logger, put __name__ for best practise
    :return: the logger
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    f_handler = logging.handlers.RotatingFileHandler("log.log", "a", maxBytes=5*1024*1024)
    c_handler = logging.StreamHandler(sys.stdout)
    f_handler.setLevel(logging.INFO - 1)
    c_handler.setLevel(logging.INFO - 1)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    f_handler.setFormatter(formatter)
    c_handler.setFormatter(formatter)
    logger.addHandler(f_handler)
    logger.addHandler(c_handler)
    logger.propagate = False  # most important setting, if this is not set to False to logging will propagate back to the root logger and print the log multiple times in different formats
    return logger


logger = get_logger("access_logger")
def log_access(method: Callable[..., Optional[Awaitable[None]]]) -> Callable[..., Optional[Awaitable[None]]]:
    """
    logging decorator
    decorate your handlers http methods with @log_access, and the access and origin will be logged to the logfile
    """

    @functools.wraps(method)
    def wrapper(self: tornado.web.RequestHandler, *args, **kwargs) -> Optional[Awaitable[None]]:
        logger.info(self.request.method + " " + self.request.uri + " from: " + (self.request.headers.get("X-Real-IP") or self.request.headers.get("X-Forwarded-For") or self.request.remote_ip))
        return method(self, *args, **kwargs)
    return wrapper
