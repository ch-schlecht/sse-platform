import pytest
import os
import shutil
import json
import contextlib
import socket
import tornado
from util import list_installed_modules, get_config_path, load_config, write_config, remove_module_files, determine_free_port
from main import make_app
from db_access import initialize_db

################################################
#               util.py test                   #
################################################
@pytest.fixture(scope="session")
def setup_util(request):
    def _setup_util():  # this member function is called when setup_util() is explicitely called (used to reproduce init state)
        if not os.path.isdir("modules/test"):
            os.makedirs("modules/test")  # generate test module
        with open("modules/test/config.json", "w") as fp:  # generate test config
            json.dump({"test": "confirm"}, fp)

    def clean():  # executed after last test was run
        if os.path.isdir("modules/test"):
            shutil.rmtree("modules/test")

    request.addfinalizer(clean)

    if not os.path.isdir("modules/test"):
        os.makedirs("modules/test")  # generate test module
    with open("modules/test/config.json", "w") as fp:  # generate test config
        json.dump({"test": "confirm"}, fp)

    return _setup_util


def test_installed_modules(setup_util):
    assert "test" in list_installed_modules()


def test_get_config_path(setup_util):
    assert os.path.join("modules", "test", "config.json") == get_config_path("test")


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
#                   API test                   #
################################################
@pytest.fixture()
def app():
    dev_mode = True  # no auth needed on the requests
    return make_app(dev_mode)


@pytest.fixture()
def setup_test_module():
    if not os.path.isdir("modules/test-module"):  # if the test module ist not there, download it
        clone("test-module")


@pytest.fixture(scope="session")
def clean_after(request):
    def _clean():
        if os.path.isdir("modules/test-module"):
            shutil.rmtree("modules/test-module")

    request.addfinalizer(_clean)


@pytest.mark.gen_test
async def test_main_handler_get(http_client, base_url):
    response = await http_client.fetch(base_url + "/main")
    assert response.code == 200


@pytest.mark.gen_test
async def test_module_handler_get_list_available(http_client, base_url):
    response = await http_client.fetch(base_url + "/modules/list_available")
    body = tornado.escape.json_decode(response.body)
    assert response.code == 200
    assert 'type' and 'modules' in body
    assert body['type'] == 'list_available_modules'


@pytest.mark.gen_test
async def test_module_handler_get_list_installed(http_client, base_url):
    response = await http_client.fetch(base_url + "/modules/list_installed")
    body = tornado.escape.json_decode(response.body)
    assert response.code == 200
    assert 'type' and 'installed_modules' in body
    assert body['type'] == 'list_installed_modules'


@pytest.mark.gen_test
async def test_module_handler_get_download(http_client, base_url, clean_after):
    if os.path.isdir("modules/test-module"):  # remove test module first before downloading
        shutil.rmtree("modules/test-module")
    response = await http_client.fetch(base_url + "/modules/download?module_name=test-module")
    body = tornado.escape.json_decode(response.body)
    assert response.code == 200
    assert 'type' and 'module' and 'success' in body
    assert body['type'] == 'installation_response'


@pytest.mark.gen_test
async def test_module_handler_get_uninstall(http_client, base_url, setup_test_module, clean_after):
    response = await http_client.fetch(base_url + "/modules/uninstall?module_name=test-module")
    body = tornado.escape.json_decode(response.body)
    assert response.code == 200
    assert 'type' and 'module' and 'success' in body
    assert body['type'] == 'uninstallation_response'


@pytest.mark.gen_test
async def test_config_handler_get_view(http_client, base_url, setup_test_module, clean_after):
    response = await http_client.fetch(base_url + "/configs/view?module_name=test-module")
    body = tornado.escape.json_decode(response.body)
    assert response.code == 200
    assert 'type' and 'module' and 'config' in body
    assert body['type'] == 'view_config'


@pytest.mark.gen_test
async def test_config_handler_post_update(http_client, base_url, setup_test_module, clean_after):
    response = await http_client.fetch(base_url + "/configs/view?module_name=test-module",
                                       method="POST",
                                       body=json.dumps({"test": "new_val", "port": 654321}))
    assert response.code == 200


@pytest.mark.gen_test
async def test_register_handler_post(http_client, base_url):
    email = "pytest@mail.de"
    nickname = "pytest"
    password = "pytest123"

    await initialize_db(False)

    response = await http_client.fetch(base_url + "/register?email={email}&nickname={nick}&password={passwd}".format(email=email, nick=nickname, passwd=password),
                                        method="POST",
                                        allow_nonstandard_methods=True,
                                        raise_error=False)
    body = tornado.escape.json_decode(response.body)
    assert response.code == 200 or response.code == 409  # 409 is also ok, user already exists
    if response.code == 200:
        assert "success" and "status" and "access_token" in body
    elif response.code == 409:
        assert "status" and "reason" in body


@pytest.mark.gen_test
async def test_login_handler_post(http_client, base_url):
    email = "pytest@mail.de"
    nickname = "pytest"
    password = "pytest123"

    await initialize_db(False)

    # do the registration call to ensure the user exists
    await http_client.fetch(base_url + "/register?email={email}&nickname={nick}&password={passwd}".format(email=email, nick=nickname, passwd=password),
                                        method="POST",
                                        allow_nonstandard_methods=True,
                                        raise_error=False)

    # the actual login call
    response = await http_client.fetch(base_url + "/login?email={email}&nickname={nick}&password={passwd}".format(email=email, nick=nickname, passwd=password),
                                        method="POST",
                                        allow_nonstandard_methods=True)
    body = tornado.escape.json_decode(response.body)
    assert response.code == 200
    assert "success" and "status" and "access_token" in body
