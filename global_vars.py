# don't change any of those values manually, they will be populated from the config when the application starts

from keycloak import KeycloakAdmin, KeycloakOpenID
port: int = 0  # port the platform is running on
config_path: str  = ""  # path to config.json
domain: str = ""  # domain the platform is running on (important for shared cookies with the modules)
servers: dict = {}  # holds active modules together with their respective ports
routing: dict = {}  # received from config, holds URI's to modules
templates_dir: str = ""  # path to module templates 
keycloak = KeycloakOpenID  # only as dummies for IDE function suggestions (correct classes with params will be set from main.py when executing the platform)
keycloak_admin = KeycloakAdmin
keycloak_client_id: str = ""
keycloak_callback_url: str = ""  # url that is send to keycloak as a callback
cookie_secret: str = "" # tornado cookie secret
