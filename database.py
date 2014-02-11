"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import sqlite3


def construct_dict(cursor):
    """ transforms the sqlite cursor rows from table format to a
        list of dictionary objects
    """
    rows = cursor.fetchall()
    return [dict((cursor.description[i][0], value)
                 for i, value in enumerate(row))
            for row in rows]

def reset_database(db_filename='simpyl.db'):
    """ deletes all data in the current database and creates a new one with a default environment entry
    """
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
    CREATE TABLE cachefile (
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
    db_con.execute("INSERT INTO environment VALUES (?);", ['default'])
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
    cursor = db_con.execute("INSERT INTO run VALUES (NULL,?,?,?,?);",
                            [timestamp, description, status, environment_name])
    run_id = cursor.lastrowid
    db_con.commit()
    return run_id


def update_run_status(db_con, run_id, status):
    """ updates a run with a new status, e.g. when it's finished
    """
    db_con.execute("UPDATE run SET status = ? WHERE id = ?;",
                   [status, run_id])
    db_con.commit()


def get_runs(db_con, environment):
    """ gets all runs from the given environment
    """
    cursor = db_con.execute("SELECT * FROM run WHERE environment_name = ?;", [environment])
    return construct_dict(cursor)


def register_procedure_call(db_con, start_time, end_time, procedure_name,
                            order, result, kwargs, run_id):
    """ adds a procedure call to the database
    """
    # end time and result are None for the time being
    cursor = db_con.execute("INSERT INTO procedure_call VALUES (NULL,?,?,?,?,?,?,?);",
                            [start_time, end_time, procedure_name, order, result, kwargs, run_id])
    procedure_call_id = cursor.lastrowid
    db_con.commit()
    return procedure_call_id


def get_procedure_calls(db_con, run_id):
    """ gets all procedure calls associated with the given run_id
    """
    cursor = db_con.execute("SELECT * FROM procedure_call WHERE run_id = ?", [run_id])
    return construct_dict(cursor)


def register_environment(db_con, environment_name):
    """ adds an environment to the database if it doesn't exist.
        returns True if a new environment was created
    """
    try:
        db_con.execute("INSERT INTO environment VALUES (?);",
                       [environment_name])
        db_con.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_environments(db_con):
    """ gets a list of all environments
    """
    cursor = db_con.execute("SELECT * FROM environment")
    return construct_dict(cursor)


def register_cached_file(db_con, filename, environment, procedure_call_id):
    """ register that a file was cached as part of the passed procedure call
        if a previous cache file exists, it will be updated
    """
    _get_current_cachefile_id_sql = """
    SELECT CF.id FROM cachefile as CF
    JOIN procedure_call as PC ON PC.id = CF.procedure_call_id
    JOIN run as R ON R.id = PC.run_id
    WHERE R.environment_name = ? and CF.filename = ?
    """

    # get the id of the current cache file if it exists
    cursor = db_con.execute(_get_current_cachefile_id_sql, [environment, filename])
    row_id = cursor.fetchone()
    # insert a new entry if it doesn't
    if row_id is None:
        db_con.execute("INSERT INTO cachefile VALUES (NULL,?,?);",
                       [filename, procedure_call_id])
    # update the existing one if it does
    else:
        # get the actual data from
        # row_id = row_id[0]
        db_con.execute("UPDATE cachefile SET procedure_call_id = ? WHERE id = ?;",
                       [procedure_call_id, row_id])

    db_con.commit()


def get_cache_filenames(db_con, environment):
    """ gets all files cached in a given environment
    """
    _get_cachefile_from_environment_sql = """
    SELECT CF.* FROM cachefile as CF
    JOIN procedure_call as PC ON PC.id = CF.procedure_call_id
    JOIN run as R ON R.id = PC.run_id
    WHERE R.environment_name = ?
    """
    cursor = db_con.execute(_get_cachefile_from_environment_sql, [environment])
    return construct_dict(cursor)