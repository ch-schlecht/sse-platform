from datetime import datetime, timedelta
from CONSTANTS import TOKEN_TTL

the_token_cache = None
def token_cache():
    global the_token_cache
    if the_token_cache is None:
        the_token_cache = Token_Cache()
    return the_token_cache

class Token_Cache:
    def __init__(self):
        self._data = {}

    def insert(self, token, user_id):
        cache_obj = {"user_id": user_id, "expires": datetime.now() + timedelta(seconds=TOKEN_TTL)}
        self._data[token] = cache_obj
        print("inserted into cache: ")
        print(cache_obj)

    def get(self, token):
        if token in self._data:
            cache_obj = self._data[token]
            if cache_obj["expires"] > datetime.now():
                self._update_ttl(token)
                return cache_obj
        else:
            return None

    def _update_ttl(self, token):
        if token in self._data:
            self._data[token]["expires"] = datetime.now() + timedelta(seconds=TOKEN_TTL)
            print("updated token ttl to: ")
            print(self._data[token])

    def _remove_expired(self):
        for token in list(self._data):
            if self._data[token]["expires"] < datetime.now():
                del self._data[token]
