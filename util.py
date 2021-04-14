from contextlib import closing
import socket

def determine_free_port() -> int:
    """
    determines a free port number to which a module can later be bound. The port number is determined by the OS

    :returns: a free port number

    """

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))  # binding a socket to 0 lets the OS assign a port
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # for threading scenario: the determined port can be used before this function returns
        return s.getsockname()[1]


class User:
    """
    model class to represent a user

    """

    def __init__(self, uid: int, email: str, nickname: str, role: str) -> None:
        self.uid = uid
        self.email = email
        self.nickname = nickname
        self.role = role
