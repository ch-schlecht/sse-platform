import json

from keycloak import KeycloakAdmin, KeycloakOpenID
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.options import options
from tornado.testing import AsyncHTTPTestCase, gen_test
import tornado.websocket

import global_vars
from main import make_app

MESSAGE_FORMAT_ERROR = "message_format_error"
KEYCLOAK_ERROR = "keycloak_error"

class TEST_USER:
    NAME = "unittest_testuser"
    EMAIL = "testuser@unittest.com"
    ROLE = "user"


def setup():
    # deal with config properties
    with open(options.config) as json_file:
        config = json.load(json_file)

    global_vars.keycloak = KeycloakOpenID(config["keycloak_base_url"], realm_name=config["keycloak_realm"], client_id=config["keycloak_client_id"],
                                          client_secret_key=config["keycloak_client_secret"])
    global_vars.keycloak_admin = KeycloakAdmin(config["keycloak_base_url"], realm_name=config["keycloak_realm"], username=config["keycloak_admin_username"],
                                               password=config["keycloak_admin_password"], verify=True, auto_refresh_token=['get', 'put', 'post', 'delete'])
    global_vars.keycloak_callback_url = config["keycloak_callback_url"]
    global_vars.config_path = options.config
    global_vars.domain = config["domain"]
    global_vars.keycloak_client_id = config["keycloak_client_id"]
    global_vars.templates_dir = config["templates_directory"]
    global_vars.cookie_secret = config["cookie_secret"]

    if "routing" in config:
        global_vars.routing = config["routing"]

    # set test mode to bypass authentication
    options.test = True


def connect_websocket(http_port):
    ws_url = tornado.httpclient.HTTPRequest("ws://localhost:{}/websocket".format(http_port), validate_cert=False, body=json.dumps({
        "type": "module_socket_connect", "module": "test_module"}), allow_nonstandard_methods=True)
    return tornado.websocket.websocket_connect(ws_url)


def validate_json_str(suspect_str: str) -> bool:
    try:
        json.loads(suspect_str)
    except:
        return False
    return True

def has_matching_resolve_id(request: dict, response: dict):
    """
    returns True if request and response have the same resolve_id, False otherwise
    """

    if ("resolve_id" not in request) or ("resolve_id" not in response):
        return False
    return request["resolve_id"] == response["resolve_id"]

def has_matching_type(request: dict, response: dict):
    """
    returns True if request's type key is the same as response type key concatenated with '_response'
    """

    if ("type" not in request) or ("type" not in response):
        return False
    return request["type"] + "_response" == response["type"]


class ApiTest(AsyncHTTPTestCase):

    def get_app(self):
        setup()
        return make_app(global_vars.cookie_secret)

    def test_main_handler_redirect(self):
        """
        expect: return 302 code to indicate no valid is present and login flow has to kick off
        """
        # switch off test mode --> expect redirect to login endpoint
        options.test = False

        # fetch will follow 302, so set follow_redirects to false because we only want to know if the 302 kicks
        response = self.fetch("/main", follow_redirects=False)
        self.assertEqual(response.code, 302)

    def test_main_handler_success(self):
        """
        expect: 200 response, containing a string, with an opening html tag (easy assertion that content is actual html)
        """
        response = self.fetch("/main")
        content = response.buffer.getvalue().decode()
        self.assertEqual(response.code, 200)
        self.assertIsInstance(content, str)
        self.assertIn("<html", content)


class BaseWebsocketTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return make_app(global_vars.cookie_secret)

    def setUp(self) -> None:
        super().setUp()
        setup()

    @gen.coroutine
    def module_start(self) -> None:
        # start the module
        request = {"type": "module_start",
                   "module_name": "test_module",
                   "port": 12345,
                   "resolve_id": "123456789"}
        self.ws_client = yield connect_websocket(self.get_http_port())
        self.ws_client.write_message(json.dumps(request))
        yield self.ws_client.read_message()

    @gen.coroutine
    def base_checks(self, request: dict, expect_success: bool) -> dict:
        yield self.module_start()

        self.ws_client.write_message(json.dumps(request))

        response = yield self.ws_client.read_message()

        # closing the socket makes the platform act like the module disconnects
        # we have to do this before we do any assertions, because if they fail, a following close wouldn't execute
        self.ws_client.close()

        # expect valid json
        is_json = validate_json_str(response)
        self.assertEqual(is_json, True)

        response = json.loads(response)

        # expect a matching resolve_id and also matching type keys
        self.assertTrue(has_matching_resolve_id(request, response))
        self.assertTrue(has_matching_type(request, response))

        # if our response is a keycloak error, theres nothing we can do about here, skip further assertions!
        if "reason" in response:
            if response["reason"] == KEYCLOAK_ERROR:
                raise RuntimeError("Keycloak Error occured, nothing we can do from our side")

        # expect a "success" key and that it has true value
        self.assertIn("success", response)
        self.assertEqual(response["success"], expect_success)

        return response


class WebsocketTestModuleStart(BaseWebsocketTestCase):
    # we cannot use the base checks here, because module_start message is always sent, which would then be sent double which would break the state of the platform

    @gen_test
    def test_websocket_module_start_success(self):
        # send valid module_start message and await response
        request = {"type": "module_start",
                   "module_name": "test_module",
                   "port": 12345,
                   "resolve_id": "123456789"}
        ws_client = yield connect_websocket(self.get_http_port())
        ws_client.write_message(json.dumps(request))
        response = yield ws_client.read_message()

        # closing the socket makes the platform act like the module disconnects
        # we have to do this before we do any assertions, because if they fail, a following close wouldn't execute
        ws_client.close()

        # expect valid json
        is_json = validate_json_str(response)
        self.assertEqual(is_json, True)

        response = json.loads(response)

        # expect a matching resolve_id and also matching type keys
        self.assertTrue(has_matching_resolve_id(request, response))
        self.assertTrue(has_matching_type(request, response))

        # expect a "success" key and that it has true value
        self.assertIn("success", response)
        self.assertEqual(response["success"], True)

        # expect resolve_id's in request and response to match
        self.assertIn("resolve_id", response)
        self.assertEqual(request["resolve_id"], response["resolve_id"])

    @gen_test
    def test_websocket_module_start_error_no_module_name(self):
        # send invalid module_start message that misses module_name and await response
        request = {"type": "module_start",
                   "port": 12345,
                   "resolve_id": "123456789"}
        ws_client = yield connect_websocket(self.get_http_port())
        ws_client.write_message(json.dumps(request))
        response = yield ws_client.read_message()

        # closing the socket makes the platform act like the module disconnects
        # we have to do this before we do any assertions, because if they fail, a following close wouldn't execute
        ws_client.close()

        # expect valid json
        is_json = validate_json_str(response)
        self.assertEqual(is_json, True)

        response = json.loads(response)

        # expect a matching resolve_id and also matching type keys
        self.assertTrue(has_matching_resolve_id(request, response))
        self.assertTrue(has_matching_type(request, response))

        # expect a "success" key and that it is False this time
        self.assertIn("success", response)
        self.assertEqual(response["success"], False)

        # expect a message format error as the reason
        self.assertIn("reason", response)
        self.assertEqual(response["reason"], MESSAGE_FORMAT_ERROR)

    @gen_test
    def test_websocket_module_start_error_no_port(self):
        # send invalid module_start message that misses port and await response
        request = {"type": "module_start",
                   "module_name": "test_module",
                   "resolve_id": "123456789"}
        ws_client = yield connect_websocket(self.get_http_port())
        ws_client.write_message(json.dumps(request))
        response = yield ws_client.read_message()

        # closing the socket makes the platform act like the module disconnects
        # we have to do this before we do any assertions, because if they fail, a following close wouldn't execute
        ws_client.close()

        # expect valid json
        is_json = validate_json_str(response)
        self.assertEqual(is_json, True)

        response = json.loads(response)

        # expect a matching resolve_id and also matching type keys
        self.assertTrue(has_matching_resolve_id(request, response))
        self.assertTrue(has_matching_type(request, response))

        # expect a "success" key and that it is False this time
        self.assertIn("success", response)
        self.assertEqual(response["success"], False)

        # expect a message format error as the reason
        self.assertIn("reason", response)
        self.assertEqual(response["reason"], MESSAGE_FORMAT_ERROR)

    @gen_test
    def test_websocket_module_start_error_already_running(self):
        # send valid module_start message first that starts the module
        request = {"type": "module_start",
                   "module_name": "test_module",
                   "port": 12345,
                   "resolve_id": "123456789"}
        ws_client = yield connect_websocket(self.get_http_port())
        ws_client.write_message(json.dumps(request))
        yield ws_client.read_message()

        # send another (valid) module_start request, but this time expecting and already_running error
        ws_client.write_message(json.dumps(request))
        response = yield ws_client.read_message()

        # closing the socket makes the platform act like the module disconnects
        # we have to do this before we do any assertions, because if they fail, a following close wouldn't execute
        ws_client.close()

        # expect valid json
        is_json = validate_json_str(response)
        self.assertEqual(is_json, True)

        response = json.loads(response)

        # expect a matching resolve_id and also matching type keys
        self.assertTrue(has_matching_resolve_id(request, response))
        self.assertTrue(has_matching_type(request, response))

        # expect a "success" key and that it is False this time
        self.assertIn("success", response)
        self.assertEqual(response["success"], False)

        # expect a message format error as the reason
        self.assertIn("reason", response)
        self.assertEqual(response["reason"], "already_running")


class WebsocketTestUserLogout(BaseWebsocketTestCase):

    @gen_test
    def test_websocket_user_logout_success(self):
        # cannot use the base checks here, because two messages are coming in
        # with the first one not being the actual response --> base assertions would break
        # so gotta do it manually

        yield self.module_start()
        request = {"type": "user_logout",
                   "resolve_id": "123456789"}
        self.ws_client.write_message(json.dumps(request))

        broadcast = yield self.ws_client.read_message()

        # second message is the actual response only to me as the requester
        response = yield self.ws_client.read_message()

        # closing the socket makes the platform act like the module disconnects
        # we have to do this before we do any assertions, because if they fail, a following close wouldn't execute
        self.ws_client.close()

        # expect valid json
        is_json = validate_json_str(broadcast)
        self.assertEqual(is_json, True)

        broadcast = json.loads(broadcast)

        # first message is the broadcast of the request to all modules, so it has to be equal to the request
        self.assertEqual(broadcast, request)
        
        # expect valid json
        is_json = validate_json_str(response)
        self.assertEqual(is_json, True)

        response = json.loads(response)

        # expect a matching resolve_id and also matching type keys
        self.assertTrue(has_matching_resolve_id(request, response))
        self.assertTrue(has_matching_type(request, response))

        # expect a "success" key and that it has true value
        self.assertIn("success", response)
        self.assertEqual(response["success"], True)


class WebsocketTestGetUser(BaseWebsocketTestCase):

    @gen_test
    def test_websocket_get_user_success(self):
        request = {"type": "get_user",
                   "resolve_id": "123456789",
                   "username": TEST_USER.NAME}

        # do the base checks that are the same for every request
        # but skip this test if a keycloak error occurs within that we cannot do anything about here
        try:
            response = yield self.base_checks(request, True)
        except RuntimeError:
            print("Keycloak Error occured, Test skipped")
            return

        # expect a "user" key
        self.assertIn("user", response)

        # expect the "user"-subdict to have all those keys: id, email, username, role
        self.assertTrue(all(key in response["user"] for key in [
                        "id", "email", "username", "role"]))

        # check the values of the user
        self.assertEqual(TEST_USER.EMAIL, response["user"]["email"])
        self.assertEqual(TEST_USER.NAME, response["user"]["username"])
        self.assertEqual(TEST_USER.ROLE, response["user"]["role"])

    @gen_test
    def test_websocket_get_user_error_missing_username(self):
        # request is missing the username key, therefore we expect failure
        request = {"type": "get_user",
                   "resolve_id": "123456789"}

        # do the base checks that are the same for every request
        # but skip this test if a keycloak error occurs within that we cannot do anything about here
        try:
            response = yield self.base_checks(request, False)
        except RuntimeError:
            print("Keycloak Error occured, Test skipped")
            return

        # expect a message format error as the reason
        self.assertIn("reason", response)
        self.assertEqual(response["reason"], MESSAGE_FORMAT_ERROR)

    
    @gen_test
    def test_websocket_get_user_list_success(self):
        request = {"type": "get_user_list",
                   "resolve_id": "123456789"}
        
        # do the base checks that are the same for every request
        # but skip this test if a keycloak error occurs within that we cannot do anything about here
        try:
            response = yield self.base_checks(request, True)
        except RuntimeError:
            print("Keycloak Error occured, Test skipped")
            return

        # expect a "users" key
        self.assertIn("users", response)

        # expect the test user to be in the user list
        self.assertIn(TEST_USER.NAME, response["users"])

        # expect the testuser-subdict to have all those keys: id, email, username, role
        self.assertTrue(all(key in response["users"][TEST_USER.NAME] for key in [
                        "id", "email", "username", "role"]))

        # check the values of the testuser
        self.assertEqual(TEST_USER.EMAIL, response["users"][TEST_USER.NAME]["email"])
        self.assertEqual(TEST_USER.NAME, response["users"][TEST_USER.NAME]["username"])
        self.assertEqual(TEST_USER.ROLE, response["users"][TEST_USER.NAME]["role"])

    @gen_test
    def test_websocket_check_permission_success(self):
        request = {"type": "check_permission",
                   "resolve_id": "123456789",
                   "username": TEST_USER.NAME}

        # do the base checks that are the same for every request
        # but skip this test if a keycloak error occurs within that we cannot do anything about here
        try:
            response = yield self.base_checks(request, True)
        except RuntimeError:
            print("Keycloak Error occured, Test skipped")
            return

        # expect a "role" key
        self.assertIn("role", response)

        # expect the value to match
        self.assertEqual(TEST_USER.ROLE, response["role"])

    @gen_test
    def test_websocket_check_permission_error_missing_username(self):
        # request misses username key
        request = {"type": "check_permission",
                   "resolve_id": "123456789"}

        # do the base checks that are the same for every request
        # but skip this test if a keycloak error occurs within that we cannot do anything about here
        try:
            response = yield self.base_checks(request, False)
        except RuntimeError:
            print("Keycloak Error occured, Test skipped")
            return

        # expect a message format error as the reason
        self.assertIn("reason", response)
        self.assertEqual(response["reason"], MESSAGE_FORMAT_ERROR)

