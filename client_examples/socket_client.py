from asyncio import get_event_loop
import json
from time import sleep
import uuid

import nacl.signing
import tornado
from tornado import gen
import tornado.httpclient
from tornado.ioloop import PeriodicCallback
from tornado.websocket import websocket_connect

import global_vars
import signing


the_websocket_client = None


async def get_socket_instance():
    global the_websocket_client
    if the_websocket_client is None:
        the_websocket_client = Client(tornado.httpclient.HTTPRequest("ws://{}:{}/websocket".format(global_vars.platform_host, global_vars.platform_port), validate_cert=False,
                                      body=json.dumps({"type": "module_socket_connect", "module": "<your_module_name_here>"}), allow_nonstandard_methods=True))
        await the_websocket_client._await_init()
    return the_websocket_client


class Client(object):
    def __init__(self, url):
        """
        Do not create an instance of this class yourself, use the provided function "get_socket_instance()" instead!
        """
        self.url = url
        self.futures = {}
        self.ws = None

    async def _await_init(self):
        await self.connect()
        PeriodicCallback(self.keep_alive, 20000).start()

    async def connect(self):
        # poll the platform for connections, until it succeeds, then break from the connection step and go into the run phase, where messages will be accepted
        while True:
            print("trying to connect to platform")
            try:
                self.ws = await websocket_connect(self.url)
                print("connected to platform")
                break
            except ConnectionRefusedError:
                print(
                    "Platform not yet ready to accept connections, retrying in 3 seconds")
                sleep(3)
                continue
        self.run()

    @gen.coroutine
    def run(self):
        while True:
            msg = yield self.ws.read_message()
            if msg is None:  # could also use a "cancel message"
                print("connection closed")
                self.ws = None
                break
            else:
                self.on_message(msg)

    def on_message(self, msg):
        json_message = tornado.escape.json_decode(msg)
        print(
            "<your_module_name_here> received message: \n {}".format(json_message))

        if "type" in json_message:
            if json_message["type"] == "signature_verification_error":
                raise RuntimeError("Platform could not validate signature")
            elif json_message["type"] == "user_login":
                pass

            elif json_message["type"] == "user_logout":
                pass

            else:
                resolve_id = json_message['resolve_id']
                if resolve_id in self.futures:
                    self.futures[resolve_id].set_result(json_message)

    def write(self, message):
        message['origin'] = "<your_module_name_here>"
        resolve_id = str(uuid.uuid4())
        message['resolve_id'] = resolve_id
        sign_key = signing.get_signing_key()
        msg_str = tornado.escape.json_encode(message)
        signed = sign_key.sign(msg_str.encode(
            "utf8"), encoder=nacl.encoding.Base64Encoder)
        signed_str = signed.decode("utf8")

        wrapped_message = {"signed_msg": signed_str,
                           "origin": "<your_module_name_here>",
                           "resolve_id": resolve_id}

        self.ws.write_message(tornado.escape.json_encode(wrapped_message))

        loop = get_event_loop()
        fut = loop.create_future()
        self.futures[resolve_id] = fut

        return fut

    async def keep_alive(self):
        if self.ws is None:
            print("Connection to platform lost, initiating reconnection")
            await self.connect()
            self.write({"type": "module_start",
                        "module_name": "<your_module_name_here>",
                        "port": global_vars.port})
