import inspect

import webserver
import run_manager as runm


class Simpyl(object):
    def __init__(self):
        self._procedures = {}
        self._proc_inits = []
        self._current_env = ''
        self._current_run = ''
        self._current_proc = ''
        self._logger = runm.stream_logger()

    def log(self, text):
        """ logs some information
        """
        self._logger.info("[user logged] {}".format(text))

    def savefig(self, title, *args, **kwargs):
        """ saves a figure to the run folder. *args and **kwargs are passed to the
            matplotlib.savefig function
        """
        runm.savefig(title, self._current_proc, self._current_run, *args, **kwargs)

    def read_cache(self, filename):
        """ loads a file from the cache.
            calls run_manager.read_cache
        """
        return runm.read_cache(filename, self._current_env)

    def write_cache(self, obj, filename):
        """ caches and object to file.
            calls run_manager.write_cache
        """
        return runm.write_cache(obj, filename, self._current_env)

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

    def start(self):
        webserver.run_server(self)
