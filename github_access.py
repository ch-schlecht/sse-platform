import os
from base64 import b64decode
from github import Github

MODULE_DIRECTORY = "modules/"
github = Github(" ae3b07d71b6285aef2333785b5fc20d703f316a1")  # personal access token, replace by dedicated account later
repo = github.get_user().get_repo("sse-platform-modules")


def list_modules():
    """
    lists all available modules (i.e. directories(!) in the repo)
    """
    return [module.name for module in repo.get_dir_contents("") if module.type == "dir"]


def remove_filename_from_path(path, filename):
    """
    helper function to parse the correct paths when cloning the module
    """
    len_filename = len(filename)
    if path[-len_filename:] == filename:
        return path[:-len_filename]
    return path


def clone(directory):
    """
    clone a module from th repo, directory is the base directory of the module (e.g. "chatsystem")
    """
    files = repo.get_dir_contents(directory)
    for contents_file in files:
        if contents_file.type == "dir":
            clone(contents_file.path)
        else:
            path = remove_filename_from_path(contents_file.path, contents_file.name)
            path = MODULE_DIRECTORY + path  # add the modules prefix
            if not os.path.exists(path):
                os.makedirs(path)

            if contents_file.name.endswith(".img") or contents_file.name.endswith(".png"):  # TODO this needs to be improved (maybe filter out file extension and make global config defines byte-like or text-like opening of the file)
                with open(MODULE_DIRECTORY + contents_file.path, 'wb') as f:
                    f.write(b64decode(contents_file.content))
            else:
                with open(MODULE_DIRECTORY + contents_file.path, 'w') as f:
                    f.write(b64decode(contents_file.content).decode())
    return True  # TODO wrap this whole thing in try/except, return False on fail
