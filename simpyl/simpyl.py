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

    def run(self, procs, description, environment=None, expand_args=None, separate_runs=True):
        """ starts a run with the listed procedures. Lists of procedures can also be passed,
            which are turned into multiple runs according to the expand_args argument
            
            procs:
                a list of (procedure, argument_dict) tuples in the form 'proc_name', {'arg_name':arg_value,...}
            description:
                Run description as a string
            environment:
                Run environment as a string. If it is None, the default environment is used.
            expand_args:
                'by_proc', 'by_run' or None
                Used to allow procedures to be called multiple times in each run,
                by passing the arguments in the procs tuples as lists instead of single values.
            
                None: each proc is called once, in order, with the arguments being treated as single values
            
                'by_proc': Each proc in the list is called multiple times, and the list is executed once.
                    All arguments for a single procedures must be iterable with with same length.
                    With each iteration i, the ith element of the argument value is passed into the procedure.
                    Use this option when procedures are largely independent and you want to execute the same
                    procedures several times with different arguments
                    e.g.
                        Simpyl.run([('foo', {'foo_arg': [1,2,3]}),
                                ('bar', {'bar_arg':[3,4]}), description='', expand_args='by_proc')
                    will call
                        foo(1), foo(2), foo(3)
                    then
                        bar(3), bar(4)

                'by_run':
                    Each proc in the list is called in order, and the list is executed N times.
                    All arguments for all procedures must be iterable with length N.
                    With each iteration i, the ith element of the argument value is passed into the procedure.
                    Use this option when one procedure will affect the next one, and you want to run through
                    a chain of procedures multiple times with different arguments. e.g.
                    e.g
                        Simpyl.run([('foo', {'foo_arg': [1,2]}),
                                ('bar', {'bar_arg':[3,4]}), description='', expand_args='by_run')
                    will call
                        foo(1), bar(3),
                    then
                        foo(2), bar(4)

            separate_runs:
                If True, and expand_args=='by_run', then each run through the list of
                procedures will be stored as a separate run.
                Ignored if expand_args is anything else.
        """

        # check the args are valid
        if expand_args not in (None, 'by_proc', 'by_run'):
            raise ValueError("expand_args must by None, 'by_proc' or 'by_run'")

        # if there's no expansion, just pass the procs to a new run
        if expand_args is None:
            # turn the procs into proc_init dictionaries
            proc_inits = _convert_to_proc_inits(procs)
            run_init = {'description': description, 'environment': environment, 'proc_inits': proc_inits}
            runm.run(self, run_init, convert_args_to_numbers=False)

        # if expanding by proc, get a list repeating all the procedures
        if expand_args == 'by_proc':
            # check that all arguments are the same length
            # first get all the lengths, proc[1] is the args dict
            lens = [[len(proc[1][k]) for k in proc[1]] for proc in procs]
            # check the first element is the same as all elements
            len_checks = [l.count(l[0]) == len(l) for l in lens]
            if not all(len_checks):
                raise ValueError("all arguments for a particular procedure must be the same length")

            # expand all the arguments in the procs then flatten the list
            # the expansion of each proc generates its own list
            proc_inits = [_convert_to_proc_inits(_expand_proc(proc)) for proc in procs]
            proc_inits = [proc for proc_expanded in proc_inits for proc in proc_expanded]

            run_init = {'description': description, 'environment': environment, 'proc_inits': proc_inits}
            runm.run(self, run_init, convert_args_to_numbers=False)

        if expand_args == 'by_run':
            # check that all arguments are the same length
            # first get all the lenghts, proc[1] is the args dict
            lens = [len(proc[1][k]) for proc in procs for k in proc[1]]
            # check the first element is the same as all elements
            if not lens.count(lens[0]) == len(lens):
                raise ValueError("all arguments for a particular procedure must be the same length")

            # expand all the procs individually
            proc_inits = [_convert_to_proc_inits(_expand_proc(proc)) for proc in procs]
            # zip over the list to get one proc for each run
            proc_inits = zip(*proc_inits)

            # if seperate runs are required, get each element and run it, otherwise flatten
            # the list and perform a single run
            if separate_runs:
                for thisrun_proc_inits in proc_inits:
                    run_init = {'description': description,
                                'environment': environment,
                                'proc_inits': proc_inits}
                    runm.run(self, run_init, convert_args_to_numbers=False)
            else:
                proc_inits = [proc for proc_expanded in proc_inits for proc in proc_expanded]
                run_init = {'description': description, 'environment': environment, 'proc_inits': proc_inits}
                runm.run(self, run_init, convert_args_to_numbers=False)


    def start(self):
        webserver.run_server(self)


def _convert_to_proc_inits(procs):
    """ takes a list of (proc_name, arguments) tuples and converts them to a list
        of proc_inits
    """
    return [{'proc_name': p[0],
             'run_order': i,
             'arguments': p[1],
             'arguments_str': runm.get_arguments_str(p[1])}
            for i, p in enumerate(procs)]


def _expand_proc(proc):
    """ takes a (proc_name, arguments) tuple and expends it into a list
        of procs, with the i_th proc having the i_th element of each
        argument in the arguments dict
    """
    return [(proc[0], map(lambda x: {x[0]: x[1][i]}, proc[1].iteritems()))
            for i in xrange(lens[0])]
