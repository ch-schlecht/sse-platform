import json
import aiopg
import CONSTANTS
import tornado
import os

database = None


def get_config():
    """
    loads the config and checks for the presence of the database connection details

    :returns: the config
    :rtype: dict

    """
    with open(CONSTANTS.CONFIG_PATH, "r") as fp:
        config = json.load(fp)
    if all(key in config for key in ("pguser", "pgpassword", "pghost", "pgport", "pgdb")):
        return config
    else:
        return None


class NoResultError(Exception):
    """
    Custom Exception thrown by SQL query functions

    """
    pass


async def initialize_db():
    """
    initializes the database, i.e. creates a connection pool and creates the neccessary tables

    """
    config = get_config()
    if config is not None:
        dsn = 'dbname={dbname} user={user} password={passwd} host={host} port={port}'.format(
            host=config['pghost'],
            port=config['pgport'],
            user=config['pguser'],
            passwd=config['pgpassword'],
            dbname=config['pgdb']
        )

        global database
        database = await aiopg.create_pool(dsn, echo=True)
        if database is not None:
            await initialize_tables()
        else:
            print("database creation failed")
    else:
        print("config misses neccessary keys")


async def initialize_tables():
    """
    loads the create_tables.sql file, if it exists and executes the table creations

    """
    if os.path.isfile("create_tables.sql"):
        with open("create_tables.sql", "r") as fp:
            schema = fp.read()
        await execute(schema)


def row_to_obj(row, cur):
    """
    Convert a SQL row to an object supporting dict and attribute access.
    Utility function not meant to be called directly

    :returns: a Python object generated from the sql result
    :rtype: object

    """
    obj = tornado.util.ObjectDict()
    for val, desc in zip(row, cur.description):
        obj[desc.name] = val
    return obj


async def execute(stmt, *args):
    """
    Execute a SQL statement without fetching any results (typically used for statements such as UPDATE, INSERT)
    Must be called with ``await execute(...)``

    :param stmt: the sql statement to execute
    :type stmt: string
    :param *args: arguments to be passed
    :type *args: Any

    """
    if database is not None:
        with (await database.cursor()) as cur:
            await cur.execute(stmt, args)
    else:
        print("database none")


async def query(stmt, *args):
    """Query the database and fetch a list of results (elements of this list can be accessed like dicts and python objects).

    Typical usage::
        results = await query(...)
    Or::
        for row in await query(...)

    :param stmt: the sql statement to execute
    :type stmt: string
    :param *args: arguments to be passed
    :type *args: Any

    :returns: list of python objects, i.e. the result set of the query
    :rtype: list

    """
    if database is not None:
        with (await database.cursor()) as cur:
            await cur.execute(stmt, args)
            return [row_to_obj(row, cur) for row in await cur.fetchall()]
    else:
        print("database is none")


async def queryone(stmt, *args):
    """Query the database, expecting exactly one result.
    Raises NoResultError if there are no results, or ValueError if
    there are more than one.

    :param stmt: the sql statement to execute
    :type stmt: string
    :param *args: arguments to be passed
    :type *args: Any

    :returns: the single result of the query
    :rtype: object

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


async def user_exists(username):
    """
    Check if the given username exists in the database.

    :param username: the username to check
    :type username: string

    :returns: True if the username exists, False otherwise
    :rtype: Bool

    """
    return bool(await query('SELECT * FROM users WHERE name=%s', username))
