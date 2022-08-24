import json
from abc import ABCMeta
from typing import Dict, Optional, Union
import os

from keycloak.exceptions import KeycloakError
import nacl.encoding
import nacl.exceptions
import nacl.signing
import tornado.escape
from tornado.options import options
import tornado.websocket

import global_vars
from logger_factory import get_logger

logger = get_logger(__name__)


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
            verify_key = nacl.signing.VerifyKey(
                verify_key_b64, encoder=nacl.encoding.Base64Encoder)
            try:  # verify message signatrue
                verified = verify_key.verify(
                    message["signed_msg"], encoder=nacl.encoding.Base64Encoder)
                original_message = tornado.escape.json_decode(
                    verified.decode("utf8"))
                if original_message["origin"] == message["origin"]:
                    return original_message
            # if the signature does it verify, BadSignatureError is thrown automatically
            except nacl.exceptions.BadSignatureError:
                return None

    def open(self):
        """
        incoming websocket connection. Add the module to the connections set.

        """

        msg = tornado.escape.json_decode(self.request.body)
        self.module_name = msg["module"]
        self.connections.add(self)
        logger.info("Client connected: {}".format(self.module_name))

    def on_close(self):
        """
        callback if the connection has been closed by the client. delete it from the connections set.

        """

        del global_vars.servers[self.module_name]
        self.connections.remove(self)
        logger.info("Client disconnected: {}".format(self.module_name))

    @classmethod
    def broadcast_message(cls, message: Union[bytes, str, Dict]):
        """
        broadcast a message to all connected clients (== modules). This function can be used from outside this handler
        by using WebsocketHandler.broadcast_message(), since it is a classmethod.

        :param message: the message to be broadcasted. check the tornado.websocket.WebSocketHandler.write_message() for further documentation on the types

        """

        for client in cls.connections:
            client.write_message(message)

    async def on_message(self, message: str):
        """
        handles incoming messages. All messages contain a "type" attribute on which they are distinguished

        :param message: the message originating from a module

        """
        # if we are in test mode, messages are not signed
        if options.test:
            json_message = tornado.escape.json_decode(message)
        else:
            # no test mode, check signature
            json_message = self._verify_msg(message)
            if json_message is None:
                logger.info("Signature Verification Error on message from: {}".format(
                    message["origin"] if "origin" in message else "no_origin_supplied"))
                self.write_message({"type": "signature_verification_error"})
                return

        logger.info("Platform received message: {}".format(
            tornado.escape.json_encode(json_message)))

        # general error handling: enforce correct message format, i.e. require "resolve_id" and "type" in every message
        if "resolve_id" not in json_message:
            self.write_message({"type": "message_format_error",
                                "description": "Message misses key 'resolve_id'"})
            return
        if "type" not in json_message:
            self.write_message({"type": "message_format_error",
                                "description": "Message misses key 'type'",
                                "resolve_id": json_message["resolve_id"]})
            return

        # handle message content
        if json_message["type"] == "module_start":
            self._module_start(json_message)
            return

        elif json_message["type"] == "user_logout":
            self._user_logout(json_message)
            return

        elif json_message['type'] == "get_user":
            self._get_user(json_message)
            return

        elif json_message['type'] == "get_user_list":
            self._get_user_list(json_message)
            return

        elif json_message["type"] == "check_permission":
            self._check_permission(json_message)
            return

        elif json_message["type"] == "get_running_modules":
            self._get_running_modules(json_message)
            return

        elif json_message["type"] == "message_module":
            self._message_module(json_message)
            return

        elif json_message["type"] == "message_module_response":
            self._message_module_response(json_message)
            return

        elif json_message["type"] == "get_template":
            self._get_template(json_message)
            return

        elif json_message["type"] == "post_template":
            self._post_template(json_message)
            return

        # default case        
        else:
            self.write_message({"type": "protocol_error",
                                "success": False,
                                "reason": "invalid request type"})
            return

    def _module_start(self, json_message: dict) -> None:
        # ensure necessary keys are in the message
        if "module_name" not in json_message:
            self.write_message({"type": "module_start_response",
                                "success": False,
                                "reason": "message_format_error",
                                "description": "Message misses key 'module_name'",
                                "resolve_id": json_message["resolve_id"]})
            return
        if "port" not in json_message:
            self.write_message({"type": "module_start_response",
                                "success": False,
                                "reason": "message_format_error",
                                "description": "Message misses key 'port'",
                                "resolve_id": json_message["resolve_id"]})
            return

        module_name = json_message["module_name"]

        if module_name in global_vars.servers:
            # module is already running
            self.write_message({"type": "module_start_response",
                                "success": False,
                                "reason": "already_running",
                                "resolve_id": json_message["resolve_id"]})
        else:
            # recognize appropriate startup
            global_vars.servers[module_name] = {"port": json_message["port"]}
            self.write_message({"type": "module_start_response",
                                "success": True,
                                "status": "recognized",
                                "resolve_id": json_message["resolve_id"]})

    def _user_logout(self, json_message: dict) -> None:
        # broadcast logout to all other modules
        self.broadcast_message(json_message)
        self.write_message({"type": "user_logout_response",
                            "success": True,
                            "resolve_id": json_message["resolve_id"]})

    def _get_user(self, json_message: dict) -> None:
        # check if username is present in the request
        if "username" not in json_message:
            self.write_message({"type": "get_user_response",
                                "success": False,
                                "reason": "message_format_error",
                                "description": "Message misses key 'username'",
                                "resolve_id": json_message["resolve_id"]})
            return

        username = json_message['username']

        # wrap keycloak requests in try/except to catch error that are not our fault here
        try:
            # refresh the token to keycloak admin portal, because it might have timed out (resulting in the following requests not succeeding)
            global_vars.keycloak_admin.refresh_token()

            # request user data from keycloak
            user_id = global_vars.keycloak_admin.get_user_id(username)
            info = global_vars.keycloak_admin.get_user(user_id)
            # keycloak returns a list of groups here, simply use first element since we rely on disjunct roles
            group_of_user = global_vars.keycloak_admin.get_user_groups(user_id)[
                0]
        except KeycloakError as e:
            logger.info(
                "Keycloak Error occured while trying to request user data: {}".format(e))
            self.write_message({"type": "get_user_response",
                                "success": False,
                                "reason": "keycloak_error",
                                "description": "Keycloak error occured, check platform logs",
                                "resolve_id": json_message["resolve_id"]})
            return

        user_payload = {"id": info["id"], "email": info["email"],
                        "username": username, "role": group_of_user["name"]}
        self.write_message({"type": "get_user_response",
                            "success": True,
                            "user": user_payload,
                            "resolve_id": json_message['resolve_id']})

    def _get_user_list(self, json_message: dict) -> None:
        # wrap keycloak requests in try/except to catch error that are not our fault here
        try:
            # refresh the token to keycloak admin portal, because it might have timed out (resulting in the following requests not succeeding)
            global_vars.keycloak_admin.refresh_token()

            # keycloak api is somewhat fiddly here, have to request groups first and afterwards members of each group separately
            user_dict = {}
            keycloak_groups_list = global_vars.keycloak_admin.get_groups()
            for group in keycloak_groups_list:
                keycloak_members_list = global_vars.keycloak_admin.get_group_members(
                    group["id"])
                for member in keycloak_members_list:
                    user_dict[member["username"]] = {"id": member["id"],
                                                     "username": member["username"],
                                                     "email": member["email"],
                                                     "role": group["name"]}
        except KeycloakError as e:
            logger.info(
                "Keycloak Error occured while trying to request user data: {}".format(e))
            self.write_message({"type": "get_user_list_response",
                                "success": False,
                                "reason": "keycloak_error",
                                "description": "Keycloak error occured, check platform logs",
                                "resolve_id": json_message["resolve_id"]})
            return

        self.write_message({"type": "get_user_list_response",
                            "success": True,
                            "users": user_dict,
                            "resolve_id": json_message['resolve_id']})

    def _check_permission(self, json_message: dict) -> None:
        # check if username is present in the request
        if "username" not in json_message:
            self.write_message({"type": "check_permission_response",
                                "success": False,
                                "reason": "message_format_error",
                                "description": "Message misses key 'username'",
                                "resolve_id": json_message["resolve_id"]})
            return

        username = json_message['username']

        # wrap keycloak requests in try/except to catch error that are not our fault here
        try:
            # refresh the token to keycloak admin portal, because it might have timed out (resulting in the following requests not succeeding)
            global_vars.keycloak_admin.refresh_token()
            user_id = global_vars.keycloak_admin.get_user_id(username)
            # keycloak returns a list of groups here, simply use first element since we rely on disjunct roles
            group_of_user = global_vars.keycloak_admin.get_user_groups(user_id)[
                0]["name"]
        except KeycloakError as e:
            logger.info(
                "Keycloak Error occured while trying to request user data: {}".format(e))
            self.write_message({"type": "check_permission_response",
                                "success": False,
                                "reason": "keycloak_error",
                                "description": "Keycloak error occured, check platform logs",
                                "resolve_id": json_message["resolve_id"]})
            return

        self.write_message({"type": "check_permission_response",
                            "success": True,
                            "username": username,
                            "role": group_of_user,
                            "resolve_id": json_message["resolve_id"]})

    def _get_running_modules(self, json_message: dict) -> None:
        data = {}
        for module_name in global_vars.servers.keys():
            data[module_name] = {
                "port": global_vars.servers[module_name]["port"]}

        self.write_message({"type": "get_running_modules_response",
                            "success": True,
                            "running_modules": data,
                            "resolve_id": json_message["resolve_id"]})

    def _message_module(self, json_message: dict) -> None:
        # check if adressee is present in the request
        if "to" not in json_message:
            self.write_message({"type": "message_module_response",
                                "success": False,
                                "reason": "message_format_error",
                                "description": "Message misses key 'to'",
                                "resolve_id": json_message["resolve_id"]})
            return

        # check if the module is online (name check) and forward them the message if yes
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

    def _message_module_response(self, json_message: dict) -> None:
        # check if adressee is present in the request
        if "to" not in json_message:
            self.write_message({"type": "message_module_response",
                                "success": False,
                                "reason": "message_format_error",
                                "description": "Message misses key 'to'",
                                "resolve_id": json_message["resolve_id"]})
            return

        # since this is a reply from a message that another module sent to it, we do not need to online check here
        # either module is still online and awaits the message, or it went offline in the middle of it, making a reply obsolete anyway
        for client in self.connections:
            if client.module_name == json_message["to"]:
                client.write_message(json_message)

    def _get_template(self, json_message: dict) -> None:
        # check if template name is present in the request
        if "template_name" not in json_message:
            self.write_message({"type": "get_template_response",
                                "success": False,
                                "reason": "message_format_error",
                                "description": "Message misses key 'template_name'",
                                "resolve_id": json_message["resolve_id"]})
            return

        template_name = json_message["template_name"]

        # template directory is not a directory, therefore we cannot have any templates
        if not os.path.isdir(global_vars.templates_dir):
            self.write_message({"type": "get_template_response",
                                "success": False,
                                "reason": "template directory not set up",
                                "resolve_id": json_message["resolve_id"]})
            return

        # template file doesnt exist
        if not os.path.isfile(global_vars.templates_dir + "/" + template_name):
            self.write_message({"type": "get_template_response",
                                "success": False,
                                "reason": "template not found",
                                "resolve_id": json_message["resolve_id"]})
            return

        # template was found, return it
        with open(global_vars.templates_dir + "/" + template_name, "r") as fp:
            template_str = fp.read()

            self.write_message({"type": "get_template_response",
                                "success": True,
                                "template": template_str,
                                "resolve_id": json_message["resolve_id"]})

    def _post_template(self, json_message: dict) -> None:
        # check if template name is present in the request
        if "template_name" not in json_message:
            self.write_message({"type": "post_template_response",
                                "success": False,
                                "reason": "message_format_error",
                                "description": "Message misses key 'template_name'",
                                "resolve_id": json_message["resolve_id"]})
            return

        template_name = json_message["template_name"]

        # if the templates directory doesnt exist, simply create it, allowing for following requests to succeed
        if not os.path.isdir(global_vars.templates_dir):
            os.mkdir(global_vars.templates_dir)

        # write template to file
        with open(global_vars.templates_dir + "/" + template_name, "w") as fp:
            fp.write(json_message["template"])

            self.write_message({"type": "post_template_response",
                                "success": True,
                                "resolve_id": json_message["resolve_id"]})
