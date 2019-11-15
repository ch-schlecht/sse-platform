import os
from CONSTANTS import MODULE_DIRECTORY


def list_installed_modules():
    return [name for name in os.listdir(MODULE_DIRECTORY)
            if os.path.isdir(os.path.join(MODULE_DIRECTORY, name))]
