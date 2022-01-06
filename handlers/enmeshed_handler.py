from abc import ABCMeta

from db_access import queryone, execute
from handlers.base_handler import BaseHandler
from logger_factory import log_access

from enmeshed_utils import *

class EnmeshedHandler(BaseHandler, metaclass=ABCMeta):
    """


    """

    @log_access
    async def get(self):
        """

        """

        if self.current_user:
            print(self.current_user)
            result = await queryone("SELECT email from users WHERE id=%s", self.current_user)
            print(result)

            id_dict = post_syncs()

            if len(id_dict) != 0:
                new_users_id = accept_changes(id_dict)
                #new_users_id = ["id1NJPNr6eoGqsDcBW9ndHSDxqZMPos36kAi"]
                send_message_to_user("Willkommen!", "Hallo vom Enmeshed Handler", new_users_id )

            s = match_enmeshed(result["email"], get_Users())

            if s:
                print(s)
                try:
                    result = await queryone("INSERT INTO enmeshed_users (id, enmeshed_id) \
                                             VALUES (%s, %s) RETURNING id",
                                             self.current_user, s["id"])
                except:
                    print("User with id %s exists." % self.current_user)

                try:
                    result = await queryone("INSERT INTO user_profile (id, firstname, lastname) \
                                             VALUES (%s, %s, %s) RETURNING id",
                                             self.current_user, s["Person.Vorname"], s["Person.Nachname"])
                except:
                    print("Profile for user already exists")
                    await execute("UPDATE user_profile SET (firstname, lastname) = ( %s, %s) WHERE id = %s RETURNING id", s["Person.Nachname"], s["Person.Vorname"], self.current_user )

            self.set_status(200)
            self.write({"status": 200,
                        "success": True})

        else:
            self.redirect("/login")
