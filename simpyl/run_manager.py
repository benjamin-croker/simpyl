import os
import errno
import logging
import time
import cPickle
import numpy as np
import matplotlib.pyplot as plt

import database as db
import settings as s


def to_number(string):
    """ takes a string and will try to convert it to an integer first,
        then a float if that fails. If neither of these work, return
        the string
    """
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return string

def run_logger(run_result_id):
    """ sets up the logger for the Simpyl object to log to an appropriate file
    """
    logger = logging.Logger('run_handler')
    handler = logging.FileHandler(
        run_path(run_result_id, s.LOGFILE_FORMAT.format(run_result_id)),
        mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(handler)
    return logger


def stream_logger():
    """ sets up the logger for the Simpyl object to log to the output
    """
    logger = logging.Logger('stream_handler')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(handler)
    return logger


def run_path(run_result_id, filename=''):
    """ gets the pathname for saving files to do with the given run
        optionally adds a filename to the path
    """
    return os.path.join('runs', run_result_id, filename)


def env_path(environment_name, filename=''):
    """ gets the pathname for saving files to do with the given environment
        optionally adds a filename to the path
    """
    return os.path.join('envs', environment_name, filename)


def create_dir_if_needed(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def savefig(title, proc_name, run_result_id, *args, **kwargs):
    """ saves a figure to the run folder. *args and **kwargs are passed to the
        matplotlib.savefig function
    """
    plt.savefig(run_path(run_result_id, s.FIGURE_FORMAT.format(proc_name, title)),
                *args, **kwargs)


def get_log(run_result_id):
    """ gets the log file for a given environment and run
    """
    with open(run_path(run_result_id, s.LOGFILE_FORMAT.format(run_result_id))) as f:
        return ''.join(f.readlines())


def read_cache(filename, environment_name):
    """ loads a file from the cache
        If the filename ends with .csv, it will be opened as a csv file
    """
    if filename[-4:] == '.csv':
        obj = np.loadtxt(env_path(environment_name, filename), delimiter=',')
    else:
        with open(env_path(environment_name, filename)) as f:
            obj = cPickle.load(f)
    return obj


def write_cache(obj, filename, environment_name):
    """ caches and object to file
        If the filename ends with .csv and the object is a numpy array,
        it is saved as a csv file
    """
    if filename[-4:] == '.csv' and type(obj) == np.ndarray:
        np.savetxt(env_path(environment_name, filename), obj, delimiter=',')
    else:
        with open(env_path(environment_name, filename), 'wb') as f:
            cPickle.dump(obj, f)

    # update the database to register the cached file
    logging.info("[simpyl logged] {} written to cache".format(filename))


def set_environment(sl, environment_name):
    """ creates all the necessary directories and database entries for a new environment
        sets up the Simpyl object for a run in the environment
    """
    # make all the directories for the environment if they don't exist
    create_dir_if_needed(env_path(environment_name))

    # register the environment in the database and set the current env
    db.register_environment(environment_name)
    sl._current_env = environment_name


def set_run(sl, run_result_id, description):
    """ creates all the necessary directories and sets up the Simpyl object for
        the run
    """
    # turn the run_result_id into a string, so it can be joined in directory names
    run_result_id = str(run_result_id)

    # create the directories for the run
    create_dir_if_needed(run_path(run_result_id))
    sl._current_run = run_result_id

    # set up logging to log to a file
    sl._logger = run_logger(run_result_id)

    # write a text file with the description as as text file
    with open(os.path.join(run_path(run_result_id),
                           s.DESCRIPTION_FORMAT.format(run_result_id)), 'w') as f:
        f.write(description)


def set_proc(sl, proc_name):
    """ sets up the simpyl object for the procedure
    """
    sl._current_proc = proc_name


def reset_sl_state(sl):
    sl._current_env = ''
    sl._current_run = ''
    sl._current_proc = ''
    sl._logger = stream_logger()


def to_run_result(run_init):
    """ creates a run_result template from a run_init
    """
    return {'id': None,
            'timestamp_start': time.time(),
            'timestamp_stop': None,
            'status': 'running',
            'description': run_init['description'],
            'environment_name': run_init['environment_name'],
            'proc_results': []}


def to_proc_result(proc_init):
    """ creates a proc_result template from a proc_init
    """
    return {'id': None,
            'proc_name': proc_init['proc_name'],
            'run_order': proc_init['run_order'],
            'timestamp_start': time.time(),
            'timestamp_stop': None,
            'result': None,
            'arguments': proc_init['arguments'],
            'arguments_str': proc_init['arguments_str'],
            'run_result_id': None}


def run(sl, run_init):
    """ set or create the current environment
    """
    set_environment(sl, run_init['environment_name'])

    # register run in database and create a run result
    run_result = to_run_result(run_init)
    run_result['id'] = db.register_run_result(run_result)
    set_run(sl, run_result['id'], run_result['description'])

    sl._logger.info("[simpyl logged] run #{} started with environment {}".format(
        run_result['id'], run_result['environment_name']))

    # call all the procedures
    for run_order, proc_init in enumerate(run_init['proc_inits']):
        # run the procedure
        proc_result = to_proc_result(proc_init)
        proc_result['run_result_id'] = run_result['id']
        set_proc(sl, proc_init['proc_name'])

        # work out the arguments, converting stings to numbers if applicable
        kwargs = dict((kw, to_number(value))
                      for kw, value in [(arg['name'], arg['value'])
                                        for arg in proc_init['arguments']])

        sl._logger.info(
            "[simpyl logged] Procedure {} called with arguments {}".format(
                proc_init['proc_name'], kwargs))
        results = sl._procedures[proc_init['proc_name']](**kwargs)

        proc_result['timestamp_stop'] = time.time()
        proc_result['result'] = str(results)

        db.register_proc_result(proc_result)
        run_result['proc_results'] += [proc_result]

    # register the run result
    run_result['timestamp_stop'] = time.time()
    run_result['status'] = 'complete'
    db.update_run_result(run_result)

    reset_sl_state(sl)
    return run_result