import inspect

import simpyl.webserver as webserver
import simpyl.run_manager as runm


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
        """ registers a procedure with the Simpyl object
        """

        def decorator(fn):
            # get argument information
            argspec = inspect.getargspec(fn)
            arguments = [{'name': arg, 'value': None} for arg in argspec.args]

            # add the default arguments, these are the at the end of the argument spec
            if argspec.defaults is not None:
                for i, v in enumerate(reversed(argspec.defaults)):
                    arguments[-(i + 1)]['value'] = v

            if procedure_name not in self._procedures:
                self._procedures[procedure_name] = fn
                # TODO: remove arguments_str key?
                self._proc_inits += [{'proc_name': procedure_name,
                                      'run_order': None,
                                      'arguments': arguments,
                                      'arguments_str': ''}]
            return fn

        return decorator

    def run(self, procs, description, environment=None):
        """ starts a run with the listed procedures
            
            procs:
                a list of (procedure, argument_dict) tuples in the form 'proc_name', {'arg_name':arg_value,...}
            description:
                Run description as a string
            environment:
                Run environment as a string. If it is None, the default environment is used.
        """
        # turn the procs into proc_init dictionaries
        proc_inits = _convert_to_proc_inits(procs)
        run_init = {'description': description, 'environment_name': environment, 'proc_inits': proc_inits}
        runm.run(self, run_init, convert_args_to_numbers=False)

    def start(self):
        webserver.run_server(self)


def _convert_to_proc_inits(procs):
    """ takes a list of (proc_name, arguments) tuples and converts them to a list
        of proc_inits
    """
    return [{'proc_name': p[0],
             'run_order': i,
             'arguments': [{'name': k, 'value': p[1][k]} for k in p[1]],
             'arguments_str': runm.get_arguments_str(p[1])}
            for i, p in enumerate(procs)]


def _expand_proc(proc):
    """ takes a (proc_name, arguments) tuple and expends it into a list
        of procs, with the i_th proc having the i_th element of each
        argument in the arguments dict
    """
    # get the number of arguments to expand over, by taking the length of the first argument
    # this assumes that all arguments are iterables with the same length
    lens = len(list(proc[1].values())[0])
    return [(proc[0], dict([(k, v[i]) for k, v in proc[1].items()]))
            for i in range(lens)]
    # return [(proc[0], dict(map(lambda (k, v): (k, v[i]), proc[1].iteritems())))
    #         for i in xrange(lens)]
