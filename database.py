"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import sqlite3

import settings as s

# the default db filename is copied so that it can be changed by reset_database
DB_FILENAME = s.DEFAULT_DB_FILENAME


def with_db(fn):
    """ decorator to handle opening and closing of database connections
    """

    def new_fn(*args, **kwargs):
        db_con = sqlite3.connect(DB_FILENAME)
        result = fn(db_con, *args, **kwargs)
        db_con.commit()
        db_con.close()
        return result

    return new_fn


def reset_database(db_filename=DB_FILENAME):
    """ deletes all data in the current database and creates a new one with a default environment entry
    """
    _create_tables_sql = ["""
    CREATE TABLE environment (
        name TEXT PRIMARY KEY
    );
    """,
                          """
    CREATE TABLE run_result (
        id INTEGER PRIMARY KEY,
        timestamp_start REAL,
        timestamp_stop REAL,
        description TEXT,
        status TEXT,
        environment_name TEXT,
        FOREIGN KEY(environment_name) REFERENCES enviromnent(name)
    );
    """,
                          """
    CREATE TABLE proc_result (
        id INTEGER PRIMARY KEY,
        proc_name TEXT,
        run_order INTEGER,
        timestamp_start REAL,
        timestamp_stop REAL,
        result TEXT,
        arguments_str TEXT,
        run_result_id INTEGER,
        FOREIGN KEY(run_result_id) REFERENCES run_result(id)
    );
    """]

    # remove the file if it exists
    try:
        os.remove(db_filename)
    except OSError:
        pass

    # set the global database name. This hack should be removed later
    global DB_FILENAME
    DB_FILENAME = db_filename

    # create the database tables
    db_con = sqlite3.connect(db_filename)
    for _create_table_sql in _create_tables_sql:
        db_con.execute(_create_table_sql)
        # create the default environment
    db_con.execute("INSERT INTO environment VALUES (?);", ['default'])
    db_con.commit()
    db_con.close()


@with_db
def register_run_result(db_con, run_result):
    """ add information about a run to the database and return the database key for it.
        The id field of run_result must be empty, as this is automatically calculated by the database

        returns the ID of the entered field, or None if it was not created
    """
    # check that the id field is empty
    if run_result['id'] is not None:
        return None

    cursor = db_con.execute("INSERT INTO run_result VALUES (NULL,?,?,?,?,?);",
                            [run_result['timestamp_start'],
                             run_result['timestamp_stop'],
                             run_result['description'],
                             run_result['status'],
                             run_result['environment_name']])
    # return the run id just created
    return cursor.lastrowid


@with_db
def update_run_result(db_con, run_result):
    """ when a run has finished, only status and timestamp changes
    """
    _update_run_result_sql = """
    UPDATE run_result SET timestamp_start=?, timestamp_stop=?, description=?, status=?,
    environment_name = ? WHERE id = ?;
    """
    db_con.execute(_update_run_result_sql, [run_result['timestamp_start'],
                                            run_result['timestamp_stop'],
                                            run_result['description'],
                                            run_result['status'],
                                            run_result['environment_name'],
                                            run_result['id']])
    return run_result['id']


@with_db
def get_run_results(db_con):
    """ gets all runs from the given environment
    """
    cursor = db_con.execute("SELECT * FROM run_result;")
    return construct_dict(cursor)


@with_db
def get_single_run_result(db_con, run_result_id):
    """ gets a specific run
    """
    cursor = db_con.execute("SELECT * FROM run_result WHERE id = ?;", [run_result_id])
    return construct_dict(cursor)


@with_db
def register_proc_result(db_con, proc_result):
    """ adds a procedure call to the database
        The id field of proc_result must be empty, as this is automatically calculated by the database

        returns the ID of the entered field, or None if it was not created
    """
    # check that the id field is empty
    if proc_result['id'] is not None:
        return None
    cursor = db_con.execute("INSERT INTO proc_result VALUES (NULL,?,?,?,?,?,?,?);",
                            [proc_result['proc_name'],
                             proc_result['run_order'],
                             proc_result['timestamp_start'],
                             proc_result['timestamp_stop'],
                             str(proc_result['result']),
                             proc_result['arguments_str'],
                             proc_result['run_result_id']])
    return cursor.lastrowid


@with_db
def get_proc_results(db_con, run_id=None):
    """ gets all procedure calls associated with the given run_id
    """
    if run_id is None:
        cursor = db_con.execute("SELECT * FROM proc_result")
    else:
        cursor = db_con.execute("SELECT * FROM proc_result WHERE run_result_id = ? ORDER BY run_order", [run_id])
    return construct_dict(cursor)


@with_db
def register_environment(db_con, environment_name):
    """ adds an environment to the database if it doesn't exist.
        returns True if a new environment was created
    """
    try:
        db_con.execute("INSERT INTO environment VALUES (?);",
                       [environment_name])
        return environment_name
    except sqlite3.IntegrityError:
        return None


@with_db
def get_environments(db_con):
    """ gets a list of all environments
    """
    cursor = db_con.execute("SELECT * FROM environment")
    return construct_dict(cursor)


def construct_dict(cursor):
    """ transforms the sqlite cursor rows from table format to a
        list of dictionary objects
    """
    rows = cursor.fetchall()
    return [dict((cursor.description[i][0], value) for i, value in enumerate(row))
            for row in rows]
