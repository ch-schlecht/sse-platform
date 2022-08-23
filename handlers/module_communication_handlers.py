import json
from abc import ABCMeta
from typing import Dict, Optional, Union
import os

import nacl.encoding
import nacl.exceptions
import nacl.signing
import tornado.escape
from tornado.options import options
import tornado.websocket

import global_vars


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
        # if we are in test mode, messages are not signed
        if options.test:
            json_message = tornado.escape.json_decode(message)
        else:
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
            self.broadcast_message(json_message)  # broadcast logout to all other modules
            self.write_message({"type":"user_logout_response",
                                "success": True,
                                "resolve_id": json_message["resolve_id"]})

        elif json_message['type'] == "get_user":
            global_vars.keycloak_admin.refresh_token()
            username = json_message['username']
            user_id = global_vars.keycloak_admin.get_user_id(username)
            info = global_vars.keycloak_admin.get_user(user_id)
            group_of_user = global_vars.keycloak_admin.get_user_groups(user_id)[0]  # this is a list, use first element since we only use disjunct roles
            user_payload = {"id": info["id"], "email": info["email"], "username": username, "role": group_of_user["name"]}
            self.write_message({"type": "get_user_response",
                                "user": user_payload,
                                "resolve_id": json_message['resolve_id']})

        elif json_message['type'] == "get_user_list":
            global_vars.keycloak_admin.refresh_token()
            user_dict = {}
            keycloak_groups_list = global_vars.keycloak_admin.get_groups()
            for group in keycloak_groups_list:
                keycloak_members_list = global_vars.keycloak_admin.get_group_members(group["id"])
                for member in keycloak_members_list:
                    user_dict[member["username"]] = {"id": member["id"], "username": member["username"], "email": member["email"], "role": group["name"]}
            self.write_message({"type": "get_user_list_response",
                                "users": user_dict,
                                "resolve_id": json_message['resolve_id']})

        elif json_message["type"] == "check_permission":
            global_vars.keycloak_admin.refresh_token()
            username = json_message["username"]
            user_id = global_vars.keycloak_admin.get_user_id(username)
            group_of_user = global_vars.keycloak_admin.get_user_groups(user_id)[0]["name"]  # this is a list, use first element since we only use disjunct groups
            self.write_message({"type": "check_permission_response",
                                "username": username,
                                "role": group_of_user,
                                "resolve_id": json_message["resolve_id"]})

        elif json_message["type"] == "get_running_modules":
            data = {}
            for module_name in global_vars.servers.keys():
                data[module_name] = {"port": global_vars.servers[module_name]["port"]}
            self.write_message({"running_modules": data})

        elif json_message["type"] == "message_module":
            # check if the module name is online (name check) and forward them the message if yes
            online = False
            for client in self.connections:
                if client.module_name == json_message["to"]:
                    client.write_message(json_message)
                    online = True
                    break

            # not found, reply module offline
            if not online:
                self.write_message({"type": "message_module_response",
                                    "success": False,
                                    "reason": "module_offline",
                                    "resolve_id": json_message["resolve_id"]})

        elif json_message["type"] == "message_module_response":
            for client in self.connections:
                if client.module_name == json_message["to"]:
                    client.write_message(json_message)

        elif json_message["type"] == "get_template":
            template_name = json_message["template_name"]
            if os.path.isdir(global_vars.templates_dir):
                if os.path.isfile(global_vars.templates_dir + "/" + template_name):
                    with open(global_vars.templates_dir + "/" + template_name, "r") as fp:
                        template_str = fp.read()

                        self.write_message({"type": "get_template_response",
                                            "template": template_str,
                                            "resolve_id": json_message["resolve_id"]})

        elif json_message["type"] == "post_template":
            template_name = json_message["template_name"]

            if not os.path.isdir(global_vars.templates_dir):
                os.mkdir(global_vars.templates_dir)

            with open(global_vars.templates_dir + "/" + template_name, "w") as fp:
                fp.write(json_message["template"])

                self.write_message({"type": "get_template_response",
                                    "success": True,
                                    "resolve_id": json_message["resolve_id"]})

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
