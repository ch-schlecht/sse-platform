# override those values on application startup

from keycloak import KeycloakOpenID
keycloak = KeycloakOpenID  # only as dummies for IDE function suggestions
port: int = 0
platform_host: str = ""
platform_port: int = 0
routing_table: dict = {}