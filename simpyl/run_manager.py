import os
import errno
import logging
import pickle
import numpy as np
import matplotlib.pyplot as plt
import glob

import simpyl.database as db
import simpyl.settings as s


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
    return os.path.join('runs', str(run_result_id), filename)


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
    plt.savefig(
        run_path(run_result_id, s.FIGURE_FORMAT.format(proc_name, title)),
        *args, **kwargs
    )


def get_log(run_result_id):
    """ gets the log file for a given run
    """
    with open(run_path(run_result_id, s.LOGFILE_FORMAT.format(run_result_id))) as f:
        return ''.join(f.readlines())


def get_figures(run_result_id):
    """ gets a list of figures for a given run
    """
    return [os.path.basename(fname) for fname in
            glob.glob(run_path(run_result_id, s.FIGURE_FORMAT.format("*", "*")))]


def get_figure(run_result_id, figure_name):
    """ gets the filename for the figure
    """
    return open(run_path(run_result_id, figure_name), 'rb')


def read_cache(filename, environment_name):
    """ loads a file from the cache
        If the filename ends with .csv, it will be opened as a csv file
    """
    if filename[-4:] == '.csv':
        obj = np.loadtxt(env_path(environment_name, filename), delimiter=',')
    else:
        with open(env_path(environment_name, filename), 'rb') as f:
            obj = pickle.load(f)
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
            pickle.dump(obj, f)

    # update the database to register the cached file
    logging.info("[simpyl logged] {} written to cache".format(filename))


def set_environment(environment_name):
    """ creates all the necessary directories and database entries for a new environment
    """
    # make all the directories for the environment if they don't exist
    create_dir_if_needed(env_path(environment_name))

    # register the environment in the database and set the current env
    db.register_environment(environment_name)


def set_run(run_result_id, description):
    """ creates all the necessary directories and sets up the Simpyl object for a run
    """
    # turn the run_result_id into a string, so it can be joined in directory names
    run_result_id = str(run_result_id)

    # create the directories for the run
    create_dir_if_needed(run_path(run_result_id))

    # write a text file with the description as as text file
    filename = os.path.join(
        run_path(run_result_id),
        s.DESCRIPTION_FORMAT.format(run_result_id)
    )
    with open(filename, 'w') as f:
        f.write(description)


def get_arguments_str(arguments):
    """ takes the arguments dictionary of a proc_init and turns it into a nicely formatted string
    """
    return ", ".join(["{}:{}".format(k, arguments[k]) for k in arguments])


def to_proc_inits(procs):
    """ takes a list of (proc_name, arguments) tuples and converts them to a list
        of proc_inits
    """
    return [{'proc_name': p[0],
             'run_order': i,
             'arguments': [{'name': k, 'value': p[1][k]} for k in p[1]],
             'arguments_str': get_arguments_str(p[1])}
            for i, p in enumerate(procs)]


def to_run_result(run_init):
    """ creates a run_result template from a run_init
    """
    return {'id': None,
            'timestamp_start': None,
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
            'run_order': None,
            'timestamp_start': None,
            'timestamp_stop': None,
            'result': None,
            'arguments': proc_init['arguments'],
            'arguments_str': proc_init['arguments_str'],
            'run_result_id': None}


def create_run_init(procs, description, environment=s.DEFAULT_ENV_NAME):
    """ takes a list of (proc_name, arguments) tuples and converts them to a
        a correctly formatted run_init
    """
    return {'description': description,
            'environment_name': environment,
            'proc_inits': to_proc_inits(procs)}