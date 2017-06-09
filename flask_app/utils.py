import sqlite3
import sys

import settings

all = ['setup_db']


def setup_db():
    """
    Create database for users
    :return: None
    """
    conn = sqlite3.connect(settings.USERBASE)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE users
    (
        username TEXT,
        password TEXT,
        email TEXT
    )""")
    cur.execute("CREATE UNIQUE INDEX users_username_uindex ON users (username);")
    conn.commit()
    conn = sqlite3.connect(settings.DATABASE)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE some
    (
        hello TEXT,
        world TEXT
    )""")
    cur.execute("INSERT INTO some (hello, world) VALUES (?, ?)", ('abc', 'def'))
    conn.commit()
    print('created')


def flush_db():
    conn = sqlite3.connect(settings.USERBASE)
    cur = conn.cursor()
    cur.execute("DELETE from users")
    conn.commit()
    print('deleted')


map = {
    'setup_db': setup_db,
    'flush_db': flush_db,
}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python utils.py COMMAND_NAME")
    f = map.get(sys.argv[1], None)
    if not f:
        print("Available commands: %s" % map.keys())
    f()
