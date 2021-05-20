import json
from abc import ABCMeta
from typing import Dict, Optional, Union

import nacl.encoding
import nacl.exceptions
import nacl.signing
import tornado.escape
import tornado.websocket

import global_vars
from db_access import query, queryone
from token_cache import token_cache


class WebsocketHandler(tornado.websocket.WebSocketHandler, metaclass=ABCMeta):
    """
    handles communication with the modules

    """

    connections = set()

    def _verify_msg(self, message: str) -> Optional[Dict]:
        """
        verify that the signature of a message is from a module that is known (i.e. its verify_key is in verify_keys.json
        and the message signature validates.

        :param message: the message to verify

        :return: the original message body as a dict (decoded json string), if the signature validates, or None otherwise

        """

        message = tornado.escape.json_decode(message)
        with open("verify_keys.json", "r") as fp:
            verify_keys = json.load(fp)

        origin = message["origin"]
        if origin in verify_keys:
            verify_key_b64 = verify_keys[origin].encode("utf8")
            verify_key = nacl.signing.VerifyKey(verify_key_b64, encoder=nacl.encoding.Base64Encoder)
            try:  # verify message signatrue
                verified = verify_key.verify(message["signed_msg"], encoder=nacl.encoding.Base64Encoder)
                original_message = tornado.escape.json_decode(verified.decode("utf8"))
                if original_message["origin"] == message["origin"]:
                    return original_message
            except nacl.exceptions.BadSignatureError:  # if the signature does it verify, BadSignatureError is thrown automatically
                print("Signature validation failed")
                return None

    def open(self):
        """
        incoming websocket connection. Add the module to the connections set.

        """

        print("client connected")
        msg = tornado.escape.json_decode(self.request.body)
        self.module_name = msg["module"]
        self.connections.add(self)

    async def on_message(self, message: str):
        """
        handles incoming messages. All messages contain a "type" attribute on which they are distinguished

        :param message: the message originating from a module

        """

        json_message = self._verify_msg(message)
        print("got message:")
        print(json_message)
        if json_message is None:
            self.write_message({"type": "signature_verification_error"})
            return

        if json_message["type"] == "module_start":
            module_name = json_message["module_name"]
            global_vars.servers[module_name] = {"port": json_message["port"]}
            self.write_message({"type": "module_start_response",
                                "status": "recognized",
                                "resolve_id": json_message["resolve_id"]})

        elif json_message["type"] == "user_logout":
            token = json_message["access_token"]
            token_cache().remove(token)
            self.broadcast_message(json_message)  # broadcast logout to all other modules
            self.write_message({"type":"user_logout_response",
                                "success": True,
                                "resolve_id": json_message["resolve_id"]})

        elif json_message['type'] == "get_user":
            username = json_message['username']
            user = await queryone("SELECT id, email, name AS username, role FROM users WHERE name = %s", username)
            self.write_message({"type": "get_user_response",
                                "user": user,
                                "resolve_id": json_message['resolve_id']})

        elif json_message['type'] == "get_user_list":
            users = await query("SELECT id, email, name AS username, role FROM users")
            ret_format = {}
            for user in users:
                ret_format[user["username"]] = user
            self.write_message({"type": "get_user_list_response",
                                "users": ret_format,
                                "resolve_id": json_message['resolve_id']})

        elif json_message["type"] == "token_validation":
            validated_user = token_cache().get(json_message["access_token"])
            if validated_user is not None:
                self.write_message({"type": "token_validation_response",
                                    "success": True,
                                    "user": {
                                        "username": validated_user["username"],
                                        "email": validated_user["email"],
                                        "user_id": validated_user["user_id"],
                                        "role": validated_user["role"],
                                        "expires": str(validated_user["expires"])
                                    },
                                    "resolve_id": json_message["resolve_id"]})
            else:
                self.write_message({"type": "token_validation_response",
                                    "success": False,
                                    "resolve_id": json_message["resolve_id"]})

        elif json_message["type"] == "update_token_ttl":
            renewed_user = token_cache().get(json_message["access_token"])
            if renewed_user is not None:
                self.write_message({"type": "update_token_ttl_response",
                            "success": True,
                            "resolve_id": json_message["resolve_id"]})
            else:
                self.write_message({"type": "update_token_ttl_response",
                            "success": False,
                            "resolve_id": json_message["resolve_id"]})

        elif json_message["type"] == "check_permission":
            username = json_message["username"]
            result = await queryone("SELECT role FROM users WHERE name = %s", username)
            self.write_message({"type": "check_permission_response",
                                "username": username,
                                "role": result["role"],
                                "resolve_id": json_message["resolve_id"]})

        elif json_message["type"] == "get_running_modules":
            data = {}
            for module_name in global_vars.servers.keys():
                data[module_name] = {"port": global_vars.servers[module_name]["port"]}
            self.write_message({"running_modules": data})

    def on_close(self):
        """
        callback if the connection has been closed by the client. delete it from the connections set.

        """

        print("Client disconnected: " + self.module_name)
        del global_vars.servers[self.module_name]
        self.connections.remove(self)

    @classmethod
    def broadcast_message(cls, message: Union[bytes, str, Dict]):
        """
        broadcast a message to all connected clients (== modules). This function can be used from outside this handler
        by using WebsocketHandler.broadcast_message(), since it is a classmethod.

        :param message: the message to be broadcasted. check the tornado.websocket.WebSocketHandler.write_message() for further documentation on the types

        """

        for client in cls.connections:
            client.write_message(message)
