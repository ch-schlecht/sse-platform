import os
import shutil
import json
import socket
from contextlib import closing
from CONSTANTS import MODULE_DIRECTORY


def list_installed_modules():
    """
    lists all installed modules, i.e. subdirectories in the modules folder

    :returns: list of installed modules
    :rtype: list of strings

    """
    return [name for name in os.listdir(MODULE_DIRECTORY)
            if os.path.isdir(os.path.join(MODULE_DIRECTORY, name))]


def remove_module_files(module_name):
    """
    deletes all files of a module, i.e. all files within the directory of the module

    :param module_name: the name of the module to be removed
    :type module_name: string
    :returns: True/False indicating success or failure
    :rtype: Boolean

    """
    if module_name is not None and module_name in list_installed_modules():
        try:
            shutil.rmtree(MODULE_DIRECTORY + module_name)
        except OSError:
            print('module file deletion failed')
            return False
    return True


def get_config_path(module_name):
    """
    Searches the module's directory tree for its config.json and returns the filepath of it

    :param module_name: the module name of which to search for the config
    :type module_name: string
    :returns: the path to the modules config.json as a string, or None, if no config is present
    :rtype: string or None

    .. note:: this method really only searches for the name "config.json"

    """
    if module_name in list_installed_modules():
        for dirpath, dirnames, filenames in os.walk(MODULE_DIRECTORY + module_name):
            for name in filenames:
                if name == "config.json":
                    return os.path.join(dirpath, name)
    return None


def load_config(config_path):
    """
    load the config (in json format) given by its path and parse it into a Python object.
    basically a wrapper around json.load(open(path))

    :param config_path: the path to the config file (can be absolute or relative)
    :type config_path: string
    :returns: the Python dictionary of the config or None, if config_path does not point to a file
    :rtype: dict or None

    """
    if config_path is not None and os.path.isfile(config_path):
        return json.load(open(config_path))
    else:
        print("config path is None")
        return None


def write_config(config_path, data):
    """
    writes data to a file. this method is supposed to override a given config by supplying
    a dict "data" and pointing it to a modules config (use :func: `get_config_path` to find a modules config path)

    :param config_path: the path of the file to be written
    :type config_path: string
    :param data: the data to write to file
    :type data: dict

    .. note:: data can potentially be any json serializable object
    .. note:: the file will be opened in write mode, i.e. if the file is present, it will be truncated, if not, it will be created
    .. seealso: :func: `get_config_path`

    """
    if config_path is not None:
        json.dump(data, open(config_path, "w"))  # TODO maybe wrap this in try/except to give user a feedback of success


def determine_free_port():
    """
    determines a free port number to which a module can later be bound. The port number is determined by the OS

    :returns: a free port number
    :rtype: int

    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))  # binding a socket to 0 lets the OS assign a port
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # for threading scenario: the determined port can be used before this function returns
        return s.getsockname()[1]


class User():
    """
    model class to represent a user

    """

    def __init__(self, uid, email, nickname, role):
        self.uid = uid
        self.email = email
        self.nickname = nickname
        self.role = role
