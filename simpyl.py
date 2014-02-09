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
        self._environment = ''

        # set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        # open a database connection
        self._db_con = db.open_db_connection('simpyl.db')

    def set_env(self, environment_name):
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
        self._environment = environment_name
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
        self.set_env(environment)

        # sort the procedures into the correct order:
        procedures = sorted(procedures, key=lambda x: x['order'])

        # register run in database and get id
        run_id = db.register_run(self._db_con, time.time(), description, 'running', self._environment)

        # set up logging to log to a file
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=os.path.join(self._environment, 'logs', 'run_{}.log'.format(run_id)))

        # call all the procedures
        for procedure in procedures:
            start_time = time.time()
            result = self.call_procedure(procedure['procedure_name'], kwargs=procedure['kwargs'])
            end_time = time.time()

            # register the procedure and result
            db.register_procedure_call(self._db_con, start_time, end_time, procedure['procedure_name'],
                                       procedure['order'], result, procedure['kwargs'], run_id)

        # update the run in the database to record its completion
        db.update_run_status(self._db_con, run_id, 'complete')

    def call_procedure(self, name, kwargs):
        """ call a procedure, all arguments must be passed as kwargs
        """
        return self._procedures[name]['fn'](**kwargs)

    def log(self, text):
        """ logs some information
        """
        logging.info(text)

    def write_cache(self, procedure_name, obj, filename):
        """ caches a file with cPickle, unless the file is a numpy array of 1 or 2 dimensions
            and the filename ends with .csv, then the file is saved as a csv
        """
        if type(obj) == np.ndarray and filename[-4:] == '.csv':
            np.savetxt(filename, obj, delimiter=',')
        else:
            with open(os.path.join(self._environment, 'cache', filename), 'wb') as f:
                cPickle.dump(obj, f)

        # save information about the cached file in the database



