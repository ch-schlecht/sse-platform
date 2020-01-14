import json
import aiopg
import CONSTANTS
import tornado
import os

database = None

def get_config():
    with open(CONSTANTS.CONFIG_PATH, "r") as fp:
        config = json.load(fp)
    if all(key in config for key in ("pguser", "pgpassword", "pghost", "pgport", "pgdb")):
        return config
    else:
        return None

class NoResultError(Exception):
    pass

async def initialize_db():
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
    if os.path.isfile("create_tables.sql"):
        with open("create_tables.sql", "r") as fp:
            schema = fp.read()
        await execute(schema)

def row_to_obj(row, cur):
    """Convert a SQL row to an object supporting dict and attribute access."""
    obj = tornado.util.ObjectDict()
    for val, desc in zip(row, cur.description):
        obj[desc.name] = val
    return obj

async def execute(stmt, *args):
    """Execute a SQL statement (typically used for non-returning types of statements such as UPDATE, INSERT)
    Must be called with ``await self.execute(...)``
    """
    if database is not None:
        with (await database.cursor()) as cur:
            await cur.execute(stmt, args)
    else:
        print("database none")

async def query(stmt, *args):
    """Query for a list of results.
    Typical usage::
        results = await self.query(...)
    Or::
        for row in await self.query(...)
    """
    if database is not None:
        with (await database.cursor()) as cur:
            await cur.execute(stmt, args)
            return [row_to_obj(row, cur) for row in await cur.fetchall()]
    else:
        print("database is none")

async def queryone(stmt, *args):
    """Query for exactly one result.
    Raises NoResultError if there are no results, or ValueError if
    there are more than one.
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
    return bool(await query('SELECT * FROM users WHERE name=%s', username))
