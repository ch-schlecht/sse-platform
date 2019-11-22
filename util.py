import os
import shutil
import json
from CONSTANTS import MODULE_DIRECTORY


def list_installed_modules():
    return [name for name in os.listdir(MODULE_DIRECTORY)
            if os.path.isdir(os.path.join(MODULE_DIRECTORY, name))]


def remove_module_files(module_name):
    if module_name is not None and module_name in list_installed_modules():
        try:
            shutil.rmtree(MODULE_DIRECTORY + module_name)
        except OSError:
            print('module file deletion failed')
            return False
    return True


def get_config_path(module_name):
    if module_name in list_installed_modules():
        for dirpath, dirnames, filenames in os.walk(MODULE_DIRECTORY + module_name):
            for name in filenames:
                if name == "config.json":
                    return os.path.join(dirpath, name)
    return None


def load_config(config_path):
    if config_path is not None:
        return json.load(open(config_path))
    else:
        print("config path is None")
        return None


def write_config(config_path, data):
    if config_path is not None:
        json.dump(data, open(config_path, "w"))  # TODO maybe wrap this in try/except to give user a feedback of success
