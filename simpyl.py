import inspect
import logging
import webserver


class Simpyl(object):
    def __init__(self):
        self._procedures = {}
        self._proc_inits = []

        # set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def log(self, text):
        """ logs some information
        """
        logging.info("[user logged] {}".format(text))

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
            self._proc_inits += [{'proc_name': procedure_name, 'arguments': arguments,
                                      'cache': caches, 'run_order': None}]
            return fn

        return decorator

    def call_procedure(self, procedure_name, kwargs):
        """ call a procedure, all arguments must be passed as kwargs
        """
        return self._procedures[procedure_name]['fn'](**kwargs)

    def get_proc_inits(self):
        return {'proc_inits': self._proc_inits}

    def start(self):
        webserver.run_server(self)
