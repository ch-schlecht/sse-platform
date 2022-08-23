import json

from keycloak import KeycloakAdmin, KeycloakOpenID
from tornado import gen
from tornado.options import options
from tornado.testing import AsyncHTTPTestCase, gen_test
import tornado.websocket

import global_vars
from main import make_app 


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


class WebsocketTest(AsyncHTTPTestCase):
    
    def get_app(self):
        setup()
        return make_app(global_vars.cookie_secret)

    def connect_websocket(self):
        self.ws_url = tornado.httpclient.HTTPRequest("ws://localhost:{}/websocket".format(self.get_http_port()), validate_cert=False, body=json.dumps({
                                                     "type": "module_socket_connect", "module": "test_module"}), allow_nonstandard_methods=True)
        return tornado.websocket.websocket_connect(self.ws_url)

    @gen_test
    def test_websocket_module_start(self):
        ws_client = yield self.connect_websocket()

        ws_client.write_message(json.dumps({"type": "module_start",
                                 "module_name": "test_module",
                                 "port": 12345,
                                 "resolve_id": "123456789"}))

        response = yield ws_client.read_message()
        print(response)
        self.assertEqual(type(response), str)
        
