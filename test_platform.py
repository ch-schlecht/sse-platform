import pytest
import os
import shutil
import json
import contextlib
import socket
from util import list_installed_modules, get_config_path, load_config, write_config, remove_module_files, determine_free_port
from github_access import list_modules, repo, remove_filename_from_path, clone

################################################
#               util.py test                   #
################################################
@pytest.fixture(scope="session")
def setup_util(request):
    def _setup_util():  # this member function is called when setup_util() is explicitely called (used to reproduce init state)
        if not os.path.isdir("modules/test"):
            os.mkdir("modules/test")  # generate test module
        with open("modules/test/config.json", "w") as fp:  # generate test config
            json.dump({"test": "confirm"}, fp)

    def clean():  # executed after last test was run
        if os.path.isdir("modules/test"):
            shutil.rmtree("modules/test")

    request.addfinalizer(clean)

    if not os.path.isdir("modules/test"):
        os.mkdir("modules/test")  # generate test module
    with open("modules/test/config.json", "w") as fp:  # generate test config
        json.dump({"test": "confirm"}, fp)

    return _setup_util


def test_installed_modules(setup_util):
    assert "test" in list_installed_modules()


def test_get_config_path(setup_util):
    assert "modules/test/config.json" == get_config_path("test")


def test_load_config(setup_util):
    config = {"test": "confirm"}
    assert config == load_config(get_config_path("test"))


def test_write_config(setup_util):
    config = {"test": "written_by_test"}
    path = get_config_path("test")
    write_config(path, config)
    assert load_config(path) == config
    setup_util()  # put the setup state back, in case of further reading tests


def test_remove_module_files(setup_util):
    remove_module_files("test")
    assert not os.path.isdir("modules/test")
    setup_util()  # reproduce setup state


def test_determine_free_port():
    port = determine_free_port()
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind(('localhost', port))
        except socket.error:
            assert False
        assert True


################################################
#              github_access.py test           #
################################################
def module_for_testing_in_remote():
    if "test-module" in repo.get_dir_contents(""):  # repo imported from github_access
        return True
    else:
        return False


@pytest.fixture(scope="session")
def setup_github_access(request):
    if not module_for_testing_in_remote():
        pass  # TODO create the test module in the remote repo

    def clean():
        if os.path.isdir("modules/test-module"):
            shutil.rmtree("modules/test-module")

    request.addfinalizer(clean)


def test_list_modules(setup_github_access):
    modules = list_modules()
    assert modules is not False  # empty list evaluates to false


def test_remove_filename_from_path():
    path = "modules/test/"
    filename = "README.md"
    path_without_filename = remove_filename_from_path(path + filename, filename)
    assert path_without_filename == path


def test_clone(setup_github_access):
    clone("test-module")
    assert os.path.exists("modules/test-module") and os.path.exists("modules/test-module/README.md")
