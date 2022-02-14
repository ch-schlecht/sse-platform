from keycloak import KeycloakAdmin, KeycloakOpenID
servers = {}  # holds active modules together with their respective ports
routing = {}  # received from config, holds URI's to modules
keycloak = KeycloakOpenID  # only as dummies for IDE function suggestions (correct classes with params will be set from main.py when executing the platform)
keycloak_admin = KeycloakAdmin
