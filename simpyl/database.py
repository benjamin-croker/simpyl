"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import sqlite3
from typing import List, Optional

import simpyl.settings as s
from simpyl import Simpyl

# the default db filename is copied so that it can be changed by reset_database
DB_PATH = os.path.join(s.DEFAULT_ENV_DIR, s.DB_FILENAME)


def with_db(fn):
    """ Decorator to handle opening and closing of database connections
        This replaces the db connection argument with at Simpyl object,
        which can be used to determine the correct database
    """

    def new_fn(sl: Simpyl, *args, **kwargs):
        db_con = sqlite3.connect(
            os.path.join(sl.get_environment(), s.DB_FILENAME)
        )
        result = fn(db_con, *args, **kwargs)
        db_con.commit()
        db_con.close()
        return result

    return new_fn


def reset_database(environment: str = s.DEFAULT_ENV_DIR):
    """ deletes all data in the current database and creates a new one with a default environment entry
    """
    _create_tables_sql = [
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
        """
    ]

    db_path = os.path.join(environment, s.DB_FILENAME)

    # remove the file if it exists
    try:
        os.remove(db_path)
    except OSError:
        pass

    # create the database tables
    db_con = sqlite3.connect(db_path)
    for _create_table_sql in _create_tables_sql:
        db_con.execute(_create_table_sql)

    db_con.commit()
    db_con.close()


@with_db
def register_run_result(db_con, run_result: dict) -> Optional[int]:
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
def update_run_result(db_con, run_result: dict) -> int:
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
def get_run_results(db_con) -> List[dict]:
    """ gets all runs from the given environment
    """
    cursor = db_con.execute("SELECT * FROM run_result;")
    runs = construct_dict(cursor)
    for run in runs:
        run['proc_results'] = get_proc_results(run_id=run['id'])
    return runs


@with_db
def get_single_run_result(db_con, run_result_id: int) -> Optional[dict]:
    """ gets a specific run
    """
    cursor = db_con.execute("SELECT * FROM run_result WHERE id = ?;", [run_result_id])
    runs = construct_dict(cursor)
    for run in runs:
        run['proc_results'] = get_proc_results(run_id=run['id'])
    if len(runs) != 1:
        return None
    return runs[0]


@with_db
def register_proc_result(db_con, proc_result: dict) -> Optional[int]:
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
def get_proc_results(db_con, run_id: int = None) -> List[dict]:
    """ gets all procedure calls associated with the given run_id
    """
    if run_id is None:
        cursor = db_con.execute("SELECT * FROM proc_result")
    else:
        cursor = db_con.execute("SELECT * FROM proc_result WHERE run_result_id = ? ORDER BY run_order", [run_id])
    return construct_dict(cursor)


def construct_dict(cursor):
    """ transforms the sqlite cursor rows from table format to a
        list of dictionary objects
    """
    rows = cursor.fetchall()
    return [dict((cursor.description[i][0], value) for i, value in enumerate(row))
            for row in rows]
