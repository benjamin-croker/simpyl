"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import sqlite3

_create_tables_sql = ["""
CREATE TABLE environment (
    name TEXT PRIMARY KEY
);
""",
                      """
CREATE TABLE run (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    description TEXT,
    status TEXT,
    environment_name TEXT,
    FOREIGN KEY environment_name REFERENCES enviromnent(name)
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
    kwargs TEXT,
    run_id INTEGER,
    FOREIGN KEY run_id REFERENCES run(id)
);
"""]

_insert_environment_sql = """
INSERT INTO environment VALUES (?);
"""

_insert_run_sql = """
INSERT INTO run VALUES (NULL,?,?,?,?);
"""

_insert_cachefile_sql = """
INSERT INTO cachefile VALUES (NULL,?,?);
"""

_insert_procedure_call_sql = """
INSERT INTO procedure_call VALUES (NULL,?,?,?,?,?,?,?)
"""

_update_run_sql = """
UPDATE run SET status = ? WHERE id = ?
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


def register_run(db_con, timestamp, description, status, environment_name):
    """ add information about a run to the database and return the database key for it
    """
    cursor = db_con.execute(_insert_run_sql, [timestamp, description, status, environment_name])
    run_id = cursor.lastrowid
    db_con.commit()
    return run_id


def update_run_status(db_con, run_id, status):
    """ updates a run with a new status, e.g. when it's finished
    """
    db_con.execute(_update_run_sql, [status, run_id])
    db_con.commit()


def register_procedure_call(db_con, start_time, end_time, procedure_name,
                            order, result, kwargs, run_id):
    """ adds a procedure call to the database
    """
    cursor = db_con.execute(_insert_procedure_call_sql, [start_time, end_time, procedure_name,
                                                         order, result, kwargs, run_id])
    procedure_call_id = cursor.lastrowid
    db_con.commit()
    return procedure_call_id


def register_environment(db_con, environment_name):
    """ adds an environment to the database if it doesn't exist.
        returns True if a new environment was created
    """
    try:
        db_con.execute(_insert_environment_sql, [environment_name])
        db_con.commit()
        return True
    except sqlite3.IntegrityError:
        return False


