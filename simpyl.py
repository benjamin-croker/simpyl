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
        self._proc_call_inits = {}

        # set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')


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

        create_dir_if_needed(os.path.join('envs', environment_name))
        create_dir_if_needed(os.path.join('envs', environment_name, 'logs'))
        create_dir_if_needed(os.path.join('envs', environment_name, 'cache'))

        # register the environment in the database and set the current env
        db.register_environment(self._db_con, environment_name)

    def add_procedure(self, procedure_name, caches=None):
        def decorator(fn):
            # get argument information
            argspec = inspect.getargspec(fn)
            arguments = [{'name': arg, 'from_cache': False, 'value': None} for arg in argspec.args]

            # add the default arguments, these are the at the end of the argument spec
            if argspec.defaults is not None:
                for i, v in enumerate(reversed(argspec.defaults)):
                    arguments[-(i + 1)]['value'] = v

            self._procedures[procedure_name] = fn
            self._proc_call_inits[procedure_name] = dict(arguments=arguments, caches=caches)
            return fn

        return decorator

    def _run(self, run_init, environment):
        # set the current environment
        self._create_environment(environment)

        # register run in database and create a run result
        run_result = {'id': None, 'timestamp_start': time.time(), 'timestamp_stop': None,
                      'status': 'running', 'description': run_init['description']}
        run_result['id'] = db.register_run_result(self._db_con, run_result, environment)

        # set up logging to log to a file
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=os.path.join(
                                environment, 'logs', 'run_{}.log'.format(run_result['id'])))
        self._simpyl_log("run #{} started in environment {}".format(run_result['id'], environment))

        # call all the procedures
        for order, proc_init in enumerate(run_init['proc_inits']):

            # run the procedure
            proc_result = {'id': None,
                           'proc_name': proc_init['proc_name'],
                           'order': proc_init['order'],
                           'timestamp_start': time.time(),
                           'timestamp_stop': None,
                           'result': None,
                           'arguments': proc_init['arguments']}

            # work out the arguments, loading them from the cache if required
            kwargs = dict((kw, value) for kw, value in
                          [(arg['name'], self._read_cache(arg['value'], environment)
                          if arg['from_cache'] else arg['value'])
                           for arg in proc_init['arguments']])

            self._simpyl_log("Procedure {} called with arguments {}".format(run_result['id'], kwargs))
            results = self._call_procedure(proc_init['proc_name'], kwargs=kwargs)

            proc_result['timestamp_stop'] = time.time()

            # store the name of the saved files instead of the raw result if it's cached
            if proc_init['caches'] is not None:
                results_str = ', '.join(proc_init['caches'])
            else:
                results_str = str(results)
            proc_result['result'] = results_str

            proc_call_id = db.register_proc_result(self._db_con, proc_result, run_result['id'])

            if proc_init['caches'] is not None:
                # make the results iterable if they're not
                if len(proc_init['caches']) == 1:
                    results = (results,)
                for result, filename in zip(results, proc_init['caches']):
                    self._write_cache(results, filename, environment, proc_call_id)

        # register the run result
        run_result['timestamp_stop'] = time.time()
        run_result['status'] = 'complete'
        db.register_run_result(self._db_con, run_result)

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
