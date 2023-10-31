import os
import errno
import logging
import pickle
import numpy as np
import matplotlib.pyplot as plt
import glob
import uuid
import shutil
from typing import List, Tuple

import simpyl.database as db
import simpyl.settings as s


def create_dir_if_needed(path: str):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


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


def run_logger(environment: str, run_result_id: int):
    """ sets up the logger for the Simpyl object to log to an appropriate file
    """
    logger = logging.Logger('run_handler')
    handler = logging.FileHandler(
        run_path(environment, run_result_id, s.LOGFILE_FORMAT.format(run_result_id)),
        mode='w'
    )
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


def run_path(environment: str, run_result_id: int, filename: str = '') -> str:
    """ gets the pathname for saving files to do with the given run
        optionally adds a filename to the path
    """
    return os.path.join(environment, 'runs', str(run_result_id), filename)


def env_path(environment: str, filename: str = '') -> str:
    """ gets the pathname for saving files to do with the given environment
        optionally adds a filename to the path
    """
    return os.path.join(environment, filename)


def get_log(environment: str, run_result_id: int) -> str:
    """ gets the log file for a given run
    """
    fn = run_path(
        environment, run_result_id, s.LOGFILE_FORMAT.format(run_result_id)
    )
    with open(fn) as f:
        return ''.join(f.readlines())


def savefig(environment: str,
            run_result_id: int,
            proc_name: str,
            title: str,
            *args, **kwargs):
    """ saves a figure to the run folder. *args and **kwargs are passed to the
        matplotlib.savefig function
    """
    # this saves the current figure
    # TODO: pass in figure as an argument
    plt.savefig(
        run_path(
            environment, run_result_id,
            s.FIGURE_FORMAT.format(proc_name, title, str(uuid.uuid4()))
        ), *args, **kwargs
    )
    plt.close('all')


def get_figures(environment: str, run_result_id: int) -> List[str]:
    """ gets a list of figures for a given run
    """
    return [
        os.path.basename(fname)
        for fname in
        glob.glob(run_path(environment, run_result_id, s.FIGURE_FORMAT.format("*", "*", "*")))
    ]


def get_figure(environment: str, run_result_id: int, figure_name: str):
    """ gets the filename for the figure
    """
    return open(run_path(environment, run_result_id, figure_name), 'rb')


def write_cache(environment: str, filename: str, obj):
    """ caches and object to file
        If the filename ends with .csv and the object is a numpy array,
        it is saved as a csv file
    """
    if filename[-4:] == '.csv' and type(obj) == np.ndarray:
        np.savetxt(env_path(environment, filename), obj, delimiter=',')
    else:
        with open(env_path(environment, filename), 'wb') as f:
            pickle.dump(obj, f)

    # update the database to register the cached file
    logging.info("[simpyl logged] {} written to cache".format(filename))


def read_cache(environment: str, filename: str):
    """ loads a file from the cache
        If the filename ends with .csv, it will be opened as a csv file
    """
    if filename[-4:] == '.csv':
        obj = np.loadtxt(env_path(environment, filename), delimiter=',')
    else:
        with open(env_path(environment, filename), 'rb') as f:
            obj = pickle.load(f)
    return obj


def reset_environment(environment: str):
    """ creates all the necessary directories and database entries for a new environment
    """
    # make all the directories for the environment if they don't exist
    create_dir_if_needed(environment)
    shutil.rmtree(environment)
    create_dir_if_needed(environment)
    db.reset_database(environment)


def set_run(environment: str, run_result_id: int, description: str):
    """ creates all the necessary directories and sets up the Simpyl object for a run
    """
    create_dir_if_needed(run_path(environment, run_result_id))

    # write a text file with the description as as text file
    filename = os.path.join(
        run_path(environment, run_result_id),
        s.DESCRIPTION_FORMAT.format(run_result_id)
    )
    with open(filename, 'w') as f:
        f.write(description)


def get_arguments_str(arguments: dict) -> str:
    """ takes the arguments dictionary of a proc_init and turns it into a nicely formatted string
    """
    return ", ".join(["{}:{}".format(k, arguments[k]) for k in arguments])


def to_proc_inits(procs: List[Tuple]) -> List[dict]:
    """ takes a list of (proc_name, arguments) tuples and converts them to a list
        of proc_inits
    """
    return [{'proc_name': p[0],
             'run_order': i,
             'arguments': [{'name': k, 'value': p[1][k]} for k in p[1]],
             'arguments_str': get_arguments_str(p[1])}
            for i, p in enumerate(procs)]


def to_run_result(run_init: dict) -> dict:
    """ creates a run_result template from a run_init
    """
    return {'id': None,
            'timestamp_start': None,
            'timestamp_stop': None,
            'status': 'pending',
            'description': run_init['description'],
            'environment': run_init['environment'],
            'proc_results': []}


def to_proc_result(proc_init: dict) -> dict:
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


def to_run_init(environment: str, procs: List[Tuple], description: str) -> dict:
    """ takes a list of (proc_name, arguments) tuples and converts them to a
        a correctly formatted run_init
    """
    return {
        'description': description,
        'environment': environment,
        'proc_inits': to_proc_inits(procs)
    }


# These functions are passed directly to the database.
register_run_result = db.register_run_result
register_proc_result = db.register_proc_result
update_run_result = db.update_run_result
get_run_results = db.get_run_results
get_single_run_result = db.get_single_run_result
