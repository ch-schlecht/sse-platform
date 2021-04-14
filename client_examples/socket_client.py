from __future__ import annotations
from asyncio import Future, get_event_loop
import json
from typing import Any, Optional
import uuid

import nacl.encoding
import tornado
import tornado.escape
import tornado.httpclient
from tornado import gen
from tornado.ioloop import PeriodicCallback
from tornado.websocket import websocket_connect

import signing
from token_cache_client import get_token_cache


the_websocket_client: Optional[Client] = None
async def get_socket_instance() -> Client:
    """
    get the singleton websocket client instance
    :return: the client

    """

    global the_websocket_client
    if the_websocket_client is None:
        the_websocket_client = Client(tornado.httpclient.HTTPRequest("ws://localhost:8888/websocket", validate_cert=False,
                                      body=json.dumps({"type": "module_socket_connect", "module": "<your_module_name_here>"}), allow_nonstandard_methods=True))
        await the_websocket_client._await_init()
    return the_websocket_client


class Client:
    def __init__(self, url) -> None:
        """
        Do not create an instance of this class yourself, use the provided function "get_socket_instance()" instead!
        """
        self.url = url
        self.futures = {}
        self.ws = None

    async def _await_init(self) -> None:
        """
        initiate the connection and set up the keep alive callback.
        This needs to be a separate function because __init__ cant be async.

        :return: None

        """

        await self.connect()
        PeriodicCallback(self.keep_alive, 20000).start()

    async def connect(self) -> None:
        """
        connect to the platform

        :return: None

        """

        print("trying to connect to platform")
        self.ws = await websocket_connect(self.url)
        print("connected to platform")
        self.run()

    @gen.coroutine
    def run(self) -> None:
        """
        coroutine loop that waits for mesages and calls on_message when they arrive

        :return: None

        """

        while True:
            msg = yield self.ws.read_message()
            if msg is None:  # could also use a "cancel message"
                print("connection closed")
                self.ws = None
                break
            else:
                self.on_message(msg)

    def on_message(self, msg: str) -> None:
        """
        handler function of new messages. Do whatever you need to do if certain messages arrive

        :param msg: the message received from the server (as a json string)

        :return: None

        """

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

    def write(self, message: Any) -> Future[str]:
        """
        Write a message to the platform. The result of this function is a future that will contain the response of the platform as a json string.
        That means you can do the following to wait for an answer of the platform:

            client = await get_socket_instance()
            response = await client.write({"your_":"json_message_here"})

        Your message will be digitally signed using your signing and verify key created by signing.py (or yourself) in order to guarantee the platform knows you.
        Make sure your verify key is present in the platforms verify_keys.json file

        :param message: the message to send to the platform. Can be any type that is json encodable by the tornado.escape.json_encode() module

        :return: Future containing the platforms response

        """

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

    async def keep_alive(self) -> None:
        if self.ws is None:
            print("reconnecting")
            await self.connect()
