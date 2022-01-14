import json
import os
from typing import Any, Dict, List, Optional

import aiopg
import bcrypt
import tornado.escape
import tornado.util

import CONSTANTS

database: Optional[aiopg.Pool] = None

def get_config() -> Optional[Dict]:
    """
    loads the config and checks for the presence of the database connection details

    :returns: the config, or None if the database credentials are not present in the config

    """

    with open(CONSTANTS.CONFIG_PATH, "r") as fp:
        config = json.load(fp)
    if all(key in config for key in ("pguser", "pgpassword", "pghost", "pgport", "pgdb")):
        return config
    else:
        return None


class NoResultError(Exception):
    """
    Custom Exception thrown by SQL query functions indicating there was no element in the result set

    """
    pass


async def initialize_db(create_admin: bool) -> None:
    """
    initializes the database, i.e. creates a connection pool and creates the neccessary tables.
    If create_admin is True, an admin account with credentials from the config will be created.

    :param create_admin: Boolean to create an admin account or not

    """

    config = get_config()
    if config:
        dsn = 'dbname={dbname} user={user} password={passwd} host={host} port={port}'.format(
            host=config['pghost'],
            port=config['pgport'],
            user=config['pguser'],
            passwd=config['pgpassword'],
            dbname=config['pgdb']
        )

        global database
        database = await aiopg.create_pool(dsn, echo=True)
        if database:
            await initialize_tables(create_admin)
        else:
            print("database creation failed")
    else:
        print("config misses neccessary keys")


async def initialize_tables(create_admin: bool) -> None:
    """
    loads the create_tables.sql file, if it exists and executes the table creations.
    If create_admin is True, an admin account with credentials from the config will be created

    :param create_admin: Boolean to create an admin account or not

    """

    if os.path.isfile("create_tables.sql"):
        with open("create_tables.sql", "r") as fp:
            schema = fp.read()
        await execute(schema)
    else:
        print("create_tables.sql is not a file or not present in the current working directory")

    if create_admin:  # create the admin account as indicated by the flag with credentials from config
        config = get_config()
        if config:
            admin_username = config['platform_admin_username']
            admin_passwd = config['platform_admin_password']
            admin_email = config['platform_admin_email']

            hashed_password = bcrypt.hashpw(tornado.escape.utf8(admin_passwd), bcrypt.gensalt(prefix=b"2a"))

            await execute("INSERT INTO users (email, name, hashed_password, role) \
                           VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                           admin_email, admin_username, tornado.escape.to_unicode(hashed_password), "admin")


def row_to_obj(row: tuple, cur: aiopg.Cursor) -> tornado.util.ObjectDict:
    """
    Convert a SQL row to an object supporting dict and attribute access.
    Utility function not meant to be called directly

    :returns: a Python object generated from the sql result

    """

    obj = tornado.util.ObjectDict()
    for val, desc in zip(row, cur.description):
        obj[desc.name] = val
    return obj


async def execute(stmt: str, *args: Any) -> None:
    """
    Execute a SQL statement without fetching any results (typically used for statements such as UPDATE, INSERT)
    Must be called with ``await execute(...)``

    :param stmt: the sql statement to execute
    :param args: arguments to be passed

    """

    if database:
        with (await database.cursor()) as cur:
            await cur.execute(stmt, args)
    else:
        print("database none")


async def query(stmt: str, *args: Any) -> Optional[List[tornado.util.ObjectDict]]:
    """
    Query the database and fetch a list of results (elements of this list can be accessed like dicts and python objects).

    Typical usage:
        results = await query(...)
    Or:
        for row in await query(...)

    :param stmt: the sql statement to execute
    :param args: arguments to be passed

    :returns: list of python objects, i.e. the result set of the query, or None if the database itself is None

    """

    if database:
        with (await database.cursor()) as cur:
            await cur.execute(stmt, args)
            return [row_to_obj(row, cur) for row in await cur.fetchall()]
    else:
        print("database is none")
        return None


async def queryone(stmt: str, *args: Any) -> Optional[tornado.util.ObjectDict]:
    """
    Query the database, expecting exactly one result.
    Raises NoResultError if there are no results, or ValueError if
    there are more than one.

    :param stmt: the sql statement to execute
    :param args: arguments to be passed

    :returns: the single result of the query

    """

    if database is not None:
        results = await query(stmt, *args)
        if len(results) == 0:
            raise NoResultError()
        elif len(results) > 1:
            raise ValueError("Expected 1 result, got %d" % len(results))
        return results[0]
    else:
        print("database is none")
        return None


async def user_exists(username: str) -> bool:
    """
    Check if the given username exists in the database.

    :param username: the username to check

    :returns: True if the username exists, False otherwise

    """

    return bool(await query('SELECT * FROM users WHERE name=%s', username))


async def is_admin(username: str) -> bool:
    """
    check if the user with the given name has the admin role

    :param username: the user to check

    :return: True if the user is an admin, False otherwise

    """

    try:
        result = await get_role(username)
        if result == "admin":
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


async def get_role(username: str) -> Optional[str]:
    """
    Query the given users role

    :param user_id: the user to check

    :return: the user's role, or None if the query did not return any result

    """

    try:
        result = await queryone("SELECT role FROM users WHERE name = %s", username)
        return result["role"]
    except Exception as e:
        print(e)
        return None


async def insert_google_user_if_not_exists(name: str, email: str, role: str = "guest") -> None:
    """
    insert a user into the db who signed in with google oauth --> no password information

    :param name: user's name
    :param email: user's email
    :param role: user's given role, defaults to guest

    :return: None

    """

    try:
        await execute(
            "INSERT INTO users(name, email, role, google_user) VALUES (%s, %s, %s, TRUE) ON CONFLICT DO NOTHING", name,
            email, role)
    except Exception as e:
        print(e)
