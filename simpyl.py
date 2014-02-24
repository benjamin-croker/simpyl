import inspect
import logging
import os
import cPickle
import numpy as np
import matplotlib.pyplot as plt

import webserver
import run_manager as runm


class Simpyl(object):
    def __init__(self):
        self._procedures = {}
        self._proc_inits = []
        self._current_env = 'default'
        self._current_run = ''

        # set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def log(self, text):
        """ logs some information
        """
        logging.info("[user logged] {}".format(text))

    def savefig(self, title, *args, **kwargs):
        """ saves a figure to the run folder. *args and **kwargs are passed to the
            matplotlib.savefig function
        """
        plt.savefig(os.path.join(
            runm.run_path(self._current_run),
            runm.FIGURE_FORMAT.format(self._current_run, title)),
                    *args, **kwargs)

    def read_cache(self, filename):
        """ loads a file from the cache. If the filename ends with .csv,
        """
        if filename[-4:] == '.csv':
            obj = np.loadtxt(os.path.join(runm.env_path(self._current_env), filename),
                             delimiter=',')
        else:
            with open(os.path.join(runm.env_path(self._current_env), filename)) as f:
                obj = cPickle.load(f)
        return obj

    def write_cache(self, obj, filename):
        """ caches a file with cPickle, unless the filename ends with .csv, then the file will
            be saved as a .csv file. This will only work if the object is a numpy array
        """
        if filename[-4:] == '.csv':
            np.savetxt(os.path.join(runm.env_path(self._current_env), filename), obj, delimiter=',')
        else:
            with open(os.path.join(runm.env_path(self._current_env), filename), 'wb') as f:
                cPickle.dump(obj, f)

        # update the database to register the cached file
        logging.info("[simpyl logged] {} written to cache".format(filename))

    def add_procedure(self, procedure_name):
        def decorator(fn):
            # get argument information
            argspec = inspect.getargspec(fn)
            arguments = [{'name': arg, 'value': None} for arg in argspec.args]

            # add the default arguments, these are the at the end of the argument spec
            if argspec.defaults is not None:
                for i, v in enumerate(reversed(argspec.defaults)):
                    arguments[-(i + 1)]['value'] = v

            self._procedures[procedure_name] = fn
            self._proc_inits += [{'proc_name': procedure_name,
                                  'run_order': None,
                                  'arguments': arguments,
                                  'arguments_str': ''}]
            return fn

        return decorator

    def call_procedure(self, procedure_name, kwargs):
        """ call a procedure, all arguments must be passed as kwargs
        """
        return self._procedures[procedure_name](**kwargs)

    def start(self):
        webserver.run_server(self)
