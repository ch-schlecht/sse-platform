PORT: int = 8888  # the port to run this platform on
CONFIG_PATH: str = "config.json"  # default, will be overridden if config is loaded from different path
TOKEN_TTL: int = 60 * 60  # ttl in secs (1 hour)
TOKEN_SIZE: int = 32  # size of access token in bytes
CLIENT_ID: str = "234734700201-pue5m9kgaem5600pb017e3jfbtn2612t.apps.googleusercontent.com"  # google client id to sign in with google
