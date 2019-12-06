import os
from base64 import b64decode
from github import Github
from CONSTANTS import MODULE_DIRECTORY

github = Github()
repo = github.get_repo("Smunfr/sse-platform-modules")


def list_modules():
    """
    lists all available modules (i.e. directories(!) in the repo)

    :returns: a list containing module names that are available
    :rtype: list of strings

    """
    return [module.name for module in repo.get_dir_contents("") if module.type == "dir"]


def remove_filename_from_path(path, filename):
    """
    helper function to parse the correct paths when cloning the module.
    removes the filename from the absolute path, leaving only the path until the directory

    :returns: the truncated path
    :rtype: string

    """
    len_filename = len(filename)
    if path[-len_filename:] == filename:
        return path[:-len_filename]
    return path


def clone(directory):
    """
    clones a module from the module-repo by supplying the name of the module.
    Strategy used is to recursively mirror the folder and file structure.
    the name of a module is considered to be the name of the top-level directory of the module

    :param directory: the name of the module to clone (top level directory name), e.g. "chatsystem"
    :type directory: string
    :returns: True to indicate succes of the download
    :rtype: Boolean

    .. note:: TODO: wrap in try/except to catch errors and return false in case

    """
    # download all the files in the current directory first
    files = repo.get_dir_contents(directory)
    for contents_file in files:
        # recursively walk only the folders
        if contents_file.type == "dir":
            clone(contents_file.path)
        else:
            # recreate the folder structure locally
            path = remove_filename_from_path(contents_file.path, contents_file.name)
            path = MODULE_DIRECTORY + path  # add the modules prefix
            if not os.path.exists(path):
                os.makedirs(path)

            # since we get the file contents in bas64 encoded strings, we now need to distinguish between string-like and byte-like files and write them
            if contents_file.name.endswith(".img") or contents_file.name.endswith(".png"):  # TODO this needs to be improved (maybe filter out file extension and make global config thath defines byte-like or text-like opening of the file)
                with open(MODULE_DIRECTORY + contents_file.path, 'wb') as f:
                    f.write(b64decode(contents_file.content))
            else:
                with open(MODULE_DIRECTORY + contents_file.path, 'w') as f:
                    f.write(b64decode(contents_file.content).decode())
    return True  # TODO wrap this whole thing in try/except, return False on fail
