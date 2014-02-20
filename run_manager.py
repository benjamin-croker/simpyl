import os
import errno
import logging
import time

import database as db


def create_dir_if_needed(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def get_log(run_result_id):
    """ gets the log file for a given environment and run
    """
    with open(os.path.join('runs', run_result_id, 'run_{}.log'.format(run_result_id))) as f:
        return ''.join(f.readlines())


def set_environment(sl, environment_name):
    """ creates all the necessary directories and database entries for a new environment
        will have no effect if the environment already exists
    """
    # make all the directories for the environment if they don't exist
    create_dir_if_needed(os.path.join('envs', environment_name))

    # register the environment in the database and set the current env
    db.register_environment(environment_name)
    sl._current_env = environment_name


def set_run(run_result_id, description):
    """ set directories for the current run
    """
    # turn the run_result_id into a string, so it can be joined in directory names
    run_result_id = str(run_result_id)

    # create the directories for the run
    create_dir_if_needed(os.path.join('runs', run_result_id))


    # set up logging to log to a file
    # remove the old log handlers
    log = logging.getLogger()  # root logger
    for hdlr in log.handlers:  # remove all old handlers
        log.removeHandler(hdlr)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=os.path.join('runs',
                                              run_result_id,
                                              'run_{}.log'.format(run_result_id)))

    # write a text file with the description as as text file
    with open(os.path.join('runs', run_result_id, 'description.txt'), 'w') as f:
        f.write(description)


def run(sl, run_init):
    """ set or create the current environment
    """
    set_environment(sl, run_init['environment_name'])

    # register run in database and create a run result
    run_result = {'id': None,
                  'timestamp_start': time.time(),
                  'timestamp_stop': None,
                  'status': 'running',
                  'description': run_init['description'],
                  'environment_name': run_init['environment_name'],
                  'proc_results': []}

    run_result['id'] = db.register_run_result(run_result)

    set_run(run_result['id'], run_result['description'])

    logging.info("[simpyl logged] run #{} started with environment {}".format(
        run_result['id'], run_result['environment_name']))

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
                       'run_result_id': run_result['id']}

        # work out the arguments, loading them from the cache if required
        kwargs = dict((kw, value)
                      for kw, value in [(arg['name'], arg['value'])
                                        for arg in proc_init['arguments']])

        sl.log("Procedure {} called with arguments {}".format(run_result['id'], kwargs))
        results = sl.call_procedure(proc_init['proc_name'], kwargs=kwargs)

        proc_result['timestamp_stop'] = time.time()
        proc_result['result'] = str(results)

        db.register_proc_result(proc_result)
        run_result['proc_results'] += [proc_result]

    # register the run result
    run_result['timestamp_stop'] = time.time()
    run_result['status'] = 'complete'
    db.update_run_result(run_result)
    return run_result