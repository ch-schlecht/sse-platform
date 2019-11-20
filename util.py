import os
import shutil
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
