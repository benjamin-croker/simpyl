import inspect
import time
import queue
import threading
from typing import List

import simpyl.run_manager as runm


class Simpyl(object):
    def __init__(self):
        # constant variables
        self._procedures = {}
        self._proc_inits = []
        # manually updated state
        self._current_env = ''
        # updated and reset each run
        self._current_run = -1
        self._current_proc = ''
        self._logger = runm.stream_logger()
        self._queue = queue.Queue()

    def reset_state(self):
        self._current_run = -1
        self._current_proc = ''
        self._logger = runm.stream_logger()

    def reset_environment(self, environment: str):
        """ creates all the necessary directories and database entries for a new environment
            and sets the current environment state
        """
        runm.reset_environment(environment)
        self._current_env = environment

    def use_environment(self, environment: str):
        # TODO: check file structure and DB is set correctly
        self._current_env = environment

    def get_environment(self) -> str:
        return self._current_env

    def set_run(self, run_result_id: int, description: str):
        """ creates all the necessary directories and sets up the Simpyl object for a run
            and sets the current run state
        """
        runm.set_run(self._current_env, run_result_id, description)
        self._current_run = run_result_id
        # set up logging to log to a file
        self._logger = runm.run_logger(self._current_env, run_result_id)

    def set_proc(self, proc_name: str):
        """ sets the current proc state
        """
        self._current_proc = proc_name

    def log(self, text: str):
        """ logs some information
        """
        self._logger.info("[user logged] {}".format(text))

    def get_log(self, run_result_id: int) -> str:
        """ Returns the log text
        """
        return runm.get_log(self._current_env, run_result_id)

    def savefig(self, title: str, *args, **kwargs):
        """ saves a figure to the run folder. *args and **kwargs are passed to the
            matplotlib.savefig function
        """
        runm.savefig(
            self._current_env, self._current_run, self._current_proc,
            title, *args, **kwargs
        )

    def get_figures(self, run_result_id: int) -> List[str]:
        return runm.get_figures(self._current_env, run_result_id)

    def get_figure(self, run_result_id: int, figure_name: str):
        return runm.get_figure(self._current_env, run_result_id, figure_name)

    def get_run_results(self) -> List[dict]:
        return runm.get_run_results(self._current_env)

    def get_single_run_result(self, run_result_id: int) -> dict:
        return runm.get_single_run_result(self._current_env, run_result_id)

    def read_cache(self, filename):
        """ loads a file from the cache.
            calls run_manager.read_cache
        """
        return runm.read_cache(self._current_env, filename)

    def write_cache(self, obj, filename):
        """ caches and object to file.
            calls run_manager.write_cache
        """
        return runm.write_cache(self._current_env, filename, obj)

    def add_procedure(self, procedure_name):
        """ registers a procedure with the Simpyl object
        """

        def decorator(fn):
            # get argument information
            argspec = inspect.getfullargspec(fn)
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

    def get_proc_inits(self):
        return self._proc_inits

    def _perform_run(self, run_init, run_result, convert_args_to_numbers):
        self.set_run(run_result['id'], run_result['description'])
        self._logger.info(
            "[simpyl logged] run #{} started with environment {}".format(
                run_result['id'], run_result['environment']
            )
        )
        run_result['timestamp_start'] = time.time()
        run_result['status'] = 'running'
        runm.update_run_result(self._current_env, run_result)

        # call all the procedures
        for run_order, proc_init in enumerate(run_init['proc_inits']):
            # run the procedure
            proc_result = runm.to_proc_result(proc_init)
            # set the run order
            proc_result['run_order'] = run_order

            proc_result['run_result_id'] = run_result['id']
            self.set_proc(proc_init['proc_name'])

            # work out the arguments, converting stings to numbers if applicable
            if convert_args_to_numbers:
                kwargs = dict(
                    (kw, runm.to_number(value))
                    for kw, value in [(arg['name'], arg['value']) for arg in proc_init['arguments']]
                )
            else:
                kwargs = dict(
                    (kw, value)
                    for kw, value in [(arg['name'], arg['value']) for arg in proc_init['arguments']]
                )

            self._logger.info(
                "[simpyl logged] Procedure {} called with arguments {}".format(
                    proc_init['proc_name'], kwargs
                )
            )
            proc_result['timestamp_start'] = time.time()
            results = self._procedures[proc_init['proc_name']](**kwargs)
            proc_result['timestamp_stop'] = time.time()
            proc_result['result'] = str(results)

            proc_result['id'] = runm.register_proc_result(self._current_env, proc_result)
            run_result['proc_results'] += [proc_result]

        # register the run result
        run_result['timestamp_stop'] = time.time()
        run_result['status'] = 'complete'
        runm.update_run_result(self._current_env, run_result)

        self.reset_state()
        return run_result

    def _queue_worker(self):
        while True:
            run_init, run_result, convert_args_to_numbers = self._queue.get()
            self._perform_run(run_init, run_result, convert_args_to_numbers)
            self._queue.task_done()

    def queue_run_init(self, run_init, convert_args_to_numbers):
        """ Sets up a run and adds it to the queue
        """
        run_result = runm.to_run_result(run_init)
        run_result['id'] = runm.register_run_result(self._current_env, run_result)
        self._queue.put((run_init, run_result, convert_args_to_numbers))

    def start_queue(self):
        threading.Thread(target=self._queue_worker, daemon=True).start()

    def run(self, procs, description):
        """ starts a run with the listed procedures
        """
        run_init = runm.to_run_init(self._current_env, procs, description)
        run_result = runm.to_run_result(run_init)
        run_result['id'] = runm.register_run_result(self._current_env, run_result)
        return self._perform_run(run_init, run_result, False)
