from abc import ABCMeta

import global_vars
from handlers.base_handler import BaseHandler
from logger_factory import log_access


class AccountDeleteHandler(BaseHandler, metaclass=ABCMeta):
    """
    Fully delete the account and all information

    """

    @log_access
    async def delete(self):
        """
        DELETE request of /delete_account
            delete the currently logged in account. To confirm this action was taken by the correct user the password
            needs to validate
            query param: password

        success:
            204
        error:
            400 -> missing query parameter
            401 -> password validation failed
            401 -> no token

        """
        if self.current_user:
            # since we don't know a password hash of him, we cannot check if it is really him, so we can't delete his account from here
            # therefore just tell the user to message an admin
            self.set_status(200)
            self.write({"status": 200,
                        "success": True,
                        "message": "contact_keycloak_admin"})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})


class RoleHandler(BaseHandler, metaclass=ABCMeta):
    """
    Read and update options for user roles

    """

    @log_access
    def get(self):
        """
        GET request of /roles
            request the role of the currently logged-in user

        success:
            200, {"type": "permission_response", "role": <str>}
        error:
            401 -> no token

        """

        if self.current_user:
            result = self.current_userinfo["resource_access"][global_vars.keycloak_client_id]["roles"]
            # is a list, but we only set one role to each user, so just take the first one
            if len(result) == 1:
                result = result[0]
            self.set_status(200)
            self.write({"type": "permission_response",
                        "role": result})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})

    @log_access
    async def post(self):
        """
        POST request of /roles
            TODO unsure if it should be possible to set the user roles of keycloak from here, therefore currently unavailable

            query param: user_name
            query param: role

        success:
            200
        error:
            410 -> moved to keycloak

        """

        self.set_status(410)
        self.write({"status": 410,
                    "reason": "moved_to_keycloak"})
        # TODO should we be able to update the roles in keycloak from here? technically its possible


class UserHandler(BaseHandler, metaclass=ABCMeta):
    """
    endpoint to request user information

    """

    @log_access
    async def get(self):
        """
        GET request of /users
            request user information of all users (id, name, email, role).
            only an account with the "admin" role can perform this action

        success:
            200, {"status": 200, "success": True, "user_list": [<user_obj>]}
        error:
            401 -> no token
            401 -> user not admin

        """

        if self.current_user:
            if self.is_current_user_admin():
                user_list = []
                keycloak_groups_list = global_vars.keycloak_admin.get_groups()
                for group in keycloak_groups_list:
                    keycloak_members_list = global_vars.keycloak_admin.get_group_members(group["id"])
                    for member in keycloak_members_list:
                        user_list.append({"id": member["id"], "name": member["username"], "email": member["email"], "role": group["name"]})
                self.set_status(200)
                self.write({"status": 200,
                            "success": True,
                            "user_list": user_list})
            else:
                self.set_status(401)
                self.write({"status": 401,
                            "reason": "user_not_admin",
                            "redirect_suggestions": ["/login"]})
        else:
            self.set_status(401)
            self.write({"status": 401,
                        "reason": "no_token",
                        "redirect_suggestions": ["/login"]})
