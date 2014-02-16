import os
import errno
import logging
import time
import cPickle

import numpy as np

import database as db


def write_cache(obj, filename, environment, procedure_call_id):
    """ caches a file with cPickle, unless the filename ends with .csv, then the file will
        be saved as a .csv file. This will only work if the
    """
    if filename[-4:] == '.csv':
        # check that the object is valid to save as
        np.savetxt(os.path.join('envs', environment, 'cache', filename), obj, delimiter=',')
    else:
        with open(os.path.join('envs', environment, 'cache', filename), 'wb') as f:
            cPickle.dump(obj, f)

    # update the database to register the cached file
    simpyl_log("{} written to cache".format(filename))
    db.register_cached_file(filename, environment, procedure_call_id)


def read_cache(filename, environment):
    """ loads a file from the cache
    """
    if filename[-4:] == '.csv':
        obj = np.loadtxt(os.path.join('envs', environment, 'cache', filename), delimiter=',')
    else:
        with open(os.path.join('envs', environment, 'cache', filename)) as f:
            obj = cPickle.load(f)
    return obj


def simpyl_log(text):
    """ logs information on behalf of simpyl
    """
    logging.info("[simpyl logged] {}".format(text))


def set_environment(environment_name):
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
    reg = db.register_environment(environment_name)
    print "DB registered {}".format(reg)


def get_environments():
    print db.get_environments()
    return {'environment_names': [e['name'] for e in db.get_environments()]}


def run(sl, run_init):
        # set or create the current environment
        set_environment(run_init['environment_name'])

        # register run in database and create a run result
        run_result = {'id': None,
                      'timestamp_start': time.time(),
                      'timestamp_stop': None,
                      'status': 'running',
                      'description': run_init['description'],
                      'environment_name': run_init['environment_name']}
        run_result['id'] = db.register_run_result(run_result)

        # set up logging to log to a file
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=os.path.join(
                                run_init['environment'],
                                'logs',
                                'run_{}.log'.format(run_result['id'])))
        simpyl_log("run #{} started in environment {}".format(run_result['id'], run_result['environment']))

        # call all the procedures
        for run_order, proc_init in enumerate(run_init['proc_inits']):

            # run the procedure
            proc_result = {'id': None,
                           'proc_name': proc_init['proc_name'],
                           'run_order': proc_init['run_order'],
                           'timestamp_start': time.time(),
                           'timestamp_stop': None,
                           'result': None,
                           'arguments': proc_init['arguments'],
                           'run_id': run_result['id']}

            # work out the arguments, loading them from the cache if required
            kwargs = dict((kw, value) for kw, value in
                          [(arg['name'], read_cache(arg['value'], run_result['environment_name'])
                          if arg['from_cache'] else arg['value'])
                           for arg in proc_init['arguments']])

            simpyl_log("Procedure {} called with arguments {}".format(run_result['id'], kwargs))
            results = sl.call_procedure(proc_init['proc_name'], kwargs=kwargs)

            proc_result['timestamp_stop'] = time.time()

            # store the name of the saved files instead of the raw result if it's cached
            if proc_init['caches'] is not None:
                results_str = ', '.join(proc_init['caches'])
            else:
                results_str = str(results)
            proc_result['result'] = results_str

            proc_result_id = db.register_proc_result(proc_result, run_result['id'])

            if proc_init['caches'] is not None:
                # make the results iterable if they're not
                if len(proc_init['caches']) == 1:
                    results = (results,)
                for result, filename in zip(results, proc_init['caches']):
                    write_cache(results, filename, run_result['environment_name'], proc_result_id)

        # register the run result
        run_result['timestamp_stop'] = time.time()
        run_result['status'] = 'complete'
        db.register_run_result(run_result)