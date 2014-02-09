import inspect
import logging
import time
import os
import errno
import cPickle

import numpy as np
import database as db


class Simpyl(object):

    def __init__(self):
        self._procedures = {}
        self._current_environment = None
        self._current_run = None
        self._current_procedure = None

        # set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        # open a database connection
        self._db_con = db.open_db_connection('simpyl.db')

    def create_environment(self, environment_name):
        """ creates all the necessary directories and database entries for a new environment
            will have no effect if the environment already exists
        """
        # make all the directories for the environment if they don't exist
        def create_dir_if_needed(path):
            try:
                os.makedirs(path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
        create_dir_if_needed(environment_name)
        create_dir_if_needed(os.path.join(environment_name, 'logs'))
        create_dir_if_needed(os.path.join(environment_name, 'cache'))

        # register the environment in the database and set the current env
        db.register_environment(self._db_con, environment_name)

    def add_procedure(self, name):
        def decorator(fn):
            self._procedures[name] = {'fn': fn, 'details': inspect.getargspec(fn)}
            return fn
        return decorator

    def list_procedures(self):
        return self._procedures

    def run(self, procedures, environment, description):
        # set the current environment
        self.create_environment(environment)
        self._current_environment = environment

        # sort the procedures into the correct order:
        procedures = sorted(procedures, key=lambda x: x['order'])

        # register run in database and get id
        run_id = db.register_run(self._db_con, time.time(), description, 'running', self._environment)
        self._current_run = run_id

        # set up logging to log to a file
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=os.path.join(self._environment, 'logs', 'run_{}.log'.format(run_id)))

        # call all the procedures
        for procedure in procedures:

            # register the procedure and result
            start_time = time.time()
            procedure_call_id = db.register_procedure_call(self._db_con, start_time,
                                                           procedure['procedure_name'],
                                                           procedure['order'],
                                                           procedure['kwargs'], run_id)
            self._current_procedure = procedure_call_id

            result = self.call_procedure(procedure['procedure_name'], kwargs=procedure['kwargs'])

            end_time = time.time()
            db.update_procedure_call_result(self._db_con, procedure_call_id, result, end_time)
            self._current_procedure = None

        # update the run in the database to record its completion
        db.update_run_status(self._db_con, run_id, 'complete')
        self._current_run = None
        self._current_environment = None

    def call_procedure(self, name, kwargs):
        """ call a procedure, all arguments must be passed as kwargs
        """
        return self._procedures[name]['fn'](**kwargs)

    def log(self, text):
        """ logs some information
        """
        logging.info(text)

    def write_cache(self, obj, filename):
        """ caches a file with cPickle, unless the file is a numpy array of 1 or 2 dimensions
            and the filename ends with .csv, then the file is saved as a csv
        """
        if type(obj) == np.ndarray and filename[-4:] == '.csv':
            np.savetxt(filename, obj, delimiter=',')
        else:
            with open(os.path.join(self._environment, 'cache', filename), 'wb') as f:
                cPickle.dump(obj, f)

        # update the database to register the cached file
        db.register_cached_file(self._db_con, filename, self._current_procedure)




