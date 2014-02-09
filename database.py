"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import sys
import sqlite3

_create_tables_sql = ["""
CREATE TABLE environment (
    id INTEGER PRIMARY KEY,
    name TEXT
);
""",
                      """
CREATE TABLE run (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    description TEXT,
    status TEXT,
    env_id INTEGER,
    FOREIGN KEY environment_id REFERENCES enviromnent(id)
);
""",
                      """
CREATE TABLE cachefiles (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    procedure_call_id INTEGER,
    FOREIGN KEY procedure_call_id REFERENCES procedure_call(id)
);
""",
                      """
CREATE TABLE procedure_call (
    id INTEGER PRIMARY KEY,
    start_time REAL,
    end_time REAL,
    procedure_name TEXT,
    order INTEGER,
    result TEXT,
    args TEXT,
    run_id INTEGER,
    FOREIGN KEY run_id REFERENCES run(id)
);
"""]

_insert_environment_sql = """
INSERT INTO environment VALUES (NULL,?);
"""

_insert_run_sql = """
INSERT INTO environment VALUES (NULL,?,?,?,?);
"""

_insert_cachefile_sql = """
INSERT INTO cachefile VALUES (NULL,?,?);
"""

_insert_procedure_call = """
INSERT INTO procedure_call VALUES (NULL,?,?,?,?,?,?,?)
"""


def reset_database(db_filename='simpyl.db'):
    """ deletes all data in the current database and creates a new one with a default environment entry
    """
    # remove the file if it exists
    try:
        os.remove(db_filename)
    except OSError:
        pass

    # create the database tables
    db_con = open_db_connection(db_filename)
    for _create_table_sql in _create_tables_sql:
        db_con.execute(_create_table_sql)
    # create the default environment
    db_con.execute(_insert_environment_sql, ['default'])
    db_con.commit()
    db_con.close()


def open_db_connection(db_filename):
    """ returns a connection to the database
    """
    return sqlite3.connect(db_filename)


def close_db_connection(db_con):
    """ closes database connection and commits any changes
    """
    db_con.commit()
    db_con.close()
