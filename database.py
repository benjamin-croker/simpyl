"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import sqlite3
import json

DB_FILENAME = 'simpyl.db'


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
    CREATE TABLE cachefile (
        id INTEGER PRIMARY KEY,
        filename TEXT,
        proc_result_id INTEGER,
        FOREIGN KEY(proc_result_id) REFERENCES proc_result(id)
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
        arguments TEXT,
        run_id INTEGER,
        FOREIGN KEY(run_id) REFERENCES run(id)
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
def register_run_result(db_con, run_result, environment_name):
    """ add information about a run to the database and return the database key for it
    """
    cursor = db_con.execute("INSERT INTO run VALUES (NULL,?,?,?,?,?);",
                            [run_result['timestamp_start'],
                             run_result['timestamp_stop'],
                             run_result['description'],
                             run_result['status'],
                             environment_name])
    # return the run id you just entered
    return cursor.lastrowid


@with_db
def update_run_result(db_con, run_result):
    """ when a run has finished, only status and timestamp changes
    """
    _update_run_result_sql = """
    UPDATE run SET timestamp_start=?, timestamp_stop=?, description=?, status=?
    environment_name = ? WHERE id = ?;
    """
    db_con.execute(_update_run_result_sql, [run_result['timestamp_start'],
                                            run_result['timestamp_stop'],
                                            run_result['description'],
                                            run_result['status'],
                                            run_result['environment_name'],
                                            run_result['id']])


@with_db
def get_runs(db_con, environment='*'):
    """ gets all runs from the given environment
    """
    cursor = db_con.execute("SELECT * FROM run_result WHERE environment_name = ?;",
                            [environment])
    return construct_dict(cursor)


@with_db
def register_proc_result(db_con, proc_result, run_id):
    """ adds a procedure call to the database
    """
    # end time and result are None for the time being
    cursor = db_con.execute("INSERT INTO proc_result VALUES (NULL,?,?,?,?,?,?,?);",
                            [proc_result['proc_name'],
                             proc_result['run_order'],
                             proc_result['timestamp_start'],
                             proc_result['timestamp_stop'],
                             str(proc_result['result']),
                             json.dumps(proc_result['arguments']),
                             run_id])
    proc_result_id = cursor.lastrowid
    return proc_result_id


@with_db
def get_proc_results(db_con, run_id='*'):
    """ gets all procedure calls associated with the given run_id
    """
    cursor = db_con.execute("SELECT * FROM proc_result WHERE run_id = ?", [run_id])
    return construct_dict(cursor, json_loads=['arguments'])


@with_db
def register_environment(db_con, environment_name):
    """ adds an environment to the database if it doesn't exist.
        returns True if a new environment was created
    """
    try:
        db_con.execute("INSERT INTO environment VALUES (?);",
                       [environment_name])
        return True
    except sqlite3.IntegrityError:
        return False


@with_db
def get_environments(db_con):
    """ gets a list of all environments
    """
    cursor = db_con.execute("SELECT * FROM environment")
    return construct_dict(cursor)


@with_db
def register_cached_file(db_con, filename, environment, proc_result_id):
    """ register that a file was cached as part of the passed procedure call
        if a previous cache file exists, it will be updated
    """
    _get_current_cachefile_id_sql = """
    SELECT CF.id FROM cachefile as CF
    JOIN proc_result as PC ON PC.id = CF.proc_result_id
    JOIN run as R ON R.id = PC.run_id
    WHERE R.environment_name = ? and CF.filename = ?
    """

    # get the id of the current cache file if it exists
    cursor = db_con.execute(_get_current_cachefile_id_sql, [environment, filename])
    row_id = cursor.fetchone()
    # insert a new entry if it doesn't
    if row_id is None:
        db_con.execute("INSERT INTO cachefile VALUES (NULL,?,?);",
                       [filename, proc_result_id])
    # update the existing one if it does
    else:
        # get the actual data from
        # row_id = row_id[0]
        db_con.execute("UPDATE cachefile SET procedure_call_id = ? WHERE id = ?;",
                       [proc_result_id, row_id])

    db_con.commit()


@with_db
def get_cache_filenames(db_con, environment='*'):
    """ gets all files cached in a given environment
    """
    _get_cachefile_from_environment_sql = """
    SELECT CF.* FROM cachefile as CF
    JOIN proc_result as PC ON PC.id = CF.proc_result_id
    JOIN run_result as R ON R.id = PC.run_id
    WHERE R.environment_name = ?
    """
    cursor = db_con.execute(_get_cachefile_from_environment_sql, [environment])
    return construct_dict(cursor)


def construct_dict(cursor, json_loads=None):
    """ transforms the sqlite cursor rows from table format to a
        list of dictionary objects

        json_loads contains a list of columns which are serialized json
        strings and should be deserialized
    """
    if not json_loads: json_loads = []
    rows = cursor.fetchall()
    return [dict((cursor.description[i][0], json.loads(value))
                 if cursor.description[i][0] in json_loads
                 else (cursor.description[i][0], value)
                 for i, value in enumerate(row))
            for row in rows]
