import tornado
import uuid
import json
import CONSTANTS
import signing
import nacl.encoding
from tornado.ioloop import PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect
from asyncio import get_event_loop
from token_cache_client import get_token_cache
from tornado.options import options


the_websocket_client = None
async def get_socket_instance():
    global the_websocket_client
    if the_websocket_client is None:
        if options.dev:
            the_websocket_client = Client("ws://localhost:88810/websocket")
        else:
            the_websocket_client = Client(tornado.httpclient.HTTPRequest("wss://localhost:" + str(CONSTANTS.PLATFORM_PORT) + "/websocket", validate_cert=False,
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
        print("trying to connect to platform")
        self.ws = await websocket_connect(self.url)
        print("connected to platform")
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
        print("<your_module_name_here> received message: ")
        print(json_message)

        if "type" in json_message:
            if json_message["type"] == "signature_verification_error":
                raise RuntimeError("Platform could not validate signature")
            elif json_message["type"] == "user_login":
                get_token_cache().insert(json_message["access_token"], json_message["username"], json_message["email"], json_message["id"], json_message["role"])

            elif json_message["type"] == "user_logout":
                get_token_cache().remove(json_message["access_token"])

            else:
                resolve_id = json_message['resolve_id']
                if resolve_id in self.futures:
                    self.futures[resolve_id].set_result(json_message)

    def write(self, message):
        message["origin"] = "<your_module_name_here>"
        resolve_id = str(uuid.uuid4())
        message["resolve_id"] = resolve_id
        sign_key = signing.get_signing_key()
        msg_str = tornado.escape.json_encode(message)
        signed = sign_key.sign(msg_str.encode("utf8"), encoder=nacl.encoding.Base64Encoder)
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
            print("reconnecting")
            await self.connect()
