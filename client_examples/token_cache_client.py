from __future__ import annotations
from typing import Dict, Optional
from datetime import datetime, timedelta

the_token_cache: Optional[Token_Cache] = None


def get_token_cache() -> Token_Cache:
    """
    Constructing function for the singleton Token_Cache class. Since it is a singleton, only use
    this function to access the class. Never create an instance yourself

    .. seealso:: :class: `Token_Cache`

    """
    global the_token_cache
    if the_token_cache is None:
        the_token_cache = Token_Cache()
    return the_token_cache


class Token_Cache:
    """
    Keeps track of active access tokens.
    When inserting a new token, an initial time to live of one hour will be granted.

    Everytime you retrieve a token and its associated user via the :func: `get` function, it is supposed that the user made an interaction with the
    server and is not inactive. Therefore his login should still be valid, though the TTL is renewed (one hour again).

    This means that if a user was inactive for more than one hour, their token expires and they need to re-login.

    .. warning:: Singleton class, never create an instance of this class yourself. Use the provided function :func: `token_cache` instead.

    .. seealso:: :func: `token_cache`

    """

    def __init__(self) -> None:
        self._data = {}

    def insert(self, token: str, username: str, email: str, id: str, role: str) -> None:
        """
        Inserts a new token into the cache, which is associated with the user behind the 'username'.
        The global time to live is one hour

        :param token: the access token
        :param username: the username of the user this token should be associated to
        :param email: the users email adress
        :param id: the users id
        :param role: the users role

        """

        self._remove_expired()
        cache_obj = {"username": username, "email": email, "id": id, "role": role, "expires": datetime.now() + timedelta(seconds=3600)}  # TODO inherit ttl value from platform
        self._data[token] = cache_obj
        print("inserted into ListServ cache: ")
        print(cache_obj)

    def get(self, token: str) -> Optional[Dict]:
        """
        Returns the cache entry for the given token, but only if the token is not expired yet. If the token is expired, None is returned instead.
        Calling the function is treated as if the user does an interaction with the server, therefore the token's TTL is renewed (one hour again)

        A cache entry is of the following exemplary form:

        .. code-block:: JSON

           {
            "username": <str>,
            "email": <str>,
            "id": <str>,
            "role": <str>,
            "expires": <datetime.datetime object>
           }

        :param token: the token to check and retrieve the entry to

        :returns: the cache entry, if the token is not expired, None otherwise

        """

        self._remove_expired()
        if token in self._data:
            cache_obj = self._data[token]
            if cache_obj["expires"] > datetime.now():
                self._update_ttl(token)  # renew ttl
                return cache_obj
        else:
            return None

    def remove(self, token: str) -> None:
        """
        Removes a token from the cache. This indicates the user is logging out and to proceed, authentication is required again

        :param token: the token to remove from the cache

        """

        self._remove_expired()
        if token in self._data:
            print("removed from ListServ cache:")
            print(self._data[token])
            del self._data[token]

    def _update_ttl(self, token: str) -> None:
        """
        Helper function to renew the TTL of the give token. Not meant to be called from outside

        .. warning:: do not call this function explicitely

        :param token: the token whose ttl should be renewed

        """

        if token in self._data:
            self._data[token]["expires"] = datetime.now() + timedelta(seconds=3600)
            print("updated ListServ token ttl to: ")
            print(self._data[token])

    def _remove_expired(self) -> None:
        """
        Helper function to remove expired tokens. This prevents the cache to become too large.
        This function is not meant to be called from outside

        .. warning:: do not call this function explicitely

        """

        for token in list(self._data):
            if self._data[token]["expires"] < datetime.now():
                del self._data[token]
