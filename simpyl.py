import inspect
import logging
import time
import os
import errno
import cPickle

import numpy as np

import database as db
import webserver


class Simpyl(object):
    def __init__(self):
        self._procedures = {}
        self._procedure_call_templates = {}

        # set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        # open a database connection
        self._db_con = db.open_db_connection('simpyl.db')

    def log(self, text):
        """ logs some information
        """
        logging.info("[user logged] {}".format(text))

    def _create_environment(self, environment_name):
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

    def _add_procedure(self, procedure_name, caches=None):
        def decorator(fn):
            # get argument information
            argspec = inspect.getargspec(fn)
            arguments = [dict(name=arg, source='manual', value=None) for arg in argspec.args]

            # add the default arguments, these are the at the end of the argument spec
            if argspec.defaults is not None:
                for i, v in enumerate(reversed(argspec.defaults)):
                    arguments[-(i + 1)]['value'] = v

            self._procedures[procedure_name] = fn
            self._procedure_call_templates[procedure_name] = dict(arguments=arguments, caches=caches)
            return fn

        return decorator

    def _run(self, procedure_calls, environment, description):
        # set the current environment
        self._create_environment(environment)

        # register run in database and get id
        run_id = db.register_run(self._db_con, time.time(), description, 'running', environment)

        # set up logging to log to a file
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=os.path.join(environment, 'logs', 'run_{}.log'.format(run_id)))
        self._simpyl_log("run #{} started in environment {}".format(run_id, environment))

        # call all the procedures
        for order, proc_call in enumerate(procedure_calls):

            # run the procedure
            # work out the arguments, loading them from the cache if required
            kwargs = dict((kw, value)
                          for kw, value in [(arg['name'],
                                             arg['value'] if arg['source'] == 'manual'
                                             else self._read_cache(arg['value'], environment))
                                            for arg in proc_call['arguments']])
            self._simpyl_log("Procedure {} called with arguments {}".format(run_id, kwargs))
            start_time = time.time()
            results = self._call_procedure(proc_call['procedure_name'], kwargs=kwargs)
            end_time = time.time()

            # store the name of the saved files instead of the raw result if it's cached
            if proc_call['caches'] is not None:
                results_str = ', '.join(proc_call['caches'])
            else:
                results_str = str(results)

            procedure_call_id = db.register_procedure_call(self._db_con, start_time, end_time,
                                                           proc_call['procedure_name'],
                                                           order, results_str,
                                                           proc_call['arguments'], run_id)

            if proc_call['caches'] is not None:
                # make the results iterable if they're not
                if len(proc_call['caches']) == 1:
                    results = (results,)
                for result, filename in zip(results, proc_call['caches']):
                    self._write_cache(results, filename, environment, procedure_call_id)

        # update the run in the database to record its completion
        db.update_run_status(self._db_con, run_id, 'complete')

    def _call_procedure(self, procedure_name, kwargs):
        """ call a procedure, all arguments must be passed as kwargs
        """
        return self._procedures[procedure_name]['fn'](**kwargs)

    def _simpyl_log(self, text):
        """ logs information on behalf of simpyl
        """
        logging.info("[simpyl logged] {}".format(text))

    def _write_cache(self, obj, filename, environment, procedure_call_id):
        """ caches a file with cPickle, unless the filename ends with .csv, then the file will
            be saved as a .csv file. This will only work if the
        """
        if filename[-4:] == '.csv':
            # check that the object is valid to save as
            np.savetxt(os.path.join(environment, 'cache', filename), obj, delimiter=',')
        else:
            with open(os.path.join(environment, 'cache', filename), 'wb') as f:
                cPickle.dump(obj, f)

        # update the database to register the cached file
        self._simpyl_log("{} written to cache".format(filename))
        db.register_cached_file(self._db_con, filename, environment, procedure_call_id)

    def _read_cache(self, filename, environment):
        """ loads a file from the cache
        """
        if filename[-4:] == '.csv':
            obj = np.loadtxt(os.path.join(environment, 'cache', filename), delimiter=',')
        else:
            with open(os.path.join(environment, 'cache', filename)) as f:
                obj = cPickle.load(f)
        return obj

    def start(self):
        webserver.run_server(self)
