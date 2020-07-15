from github import Github


def get_repo():
    try:
        github = Github()
        repo = github.get_repo("Smunfr/sse-platform-modules")
    except Exception as e:
        print(e)
        repo = None
    finally:
        return repo


def list_modules():
    """
    lists all available modules (i.e. directories(!) in the repo)

    :returns: a list containing module names that are available
    :rtype: list of strings

    """
    repo = get_repo()
    if repo:
        return [module.name for module in repo.get_dir_contents("") if module.type == "dir"]
    else:
        return None


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
