import inspect
import logging
import time

import database as db


class Simpyl(object):
    def __init__(self):
        self._procedures = {}
        self.env = 'default'
        # set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
        # open a database connection
        self._db_con = db.open_db_connection('simpyl.db')

    def add_procedure(self, name):
        def decorator(fn):
            self._procedures[name] = {'fn': fn, 'details': inspect.getargspec(fn)}
            return fn
        return decorator

    def list_procedures(self):
        return self._procedures

    def log(self, text):
        logging.info(text)

    def run(self, procedures, environment, description):
        # sort the procedures into the correct order:
        procedures = sorted(procedures, key=lambda x: x['order'])

        # register run in database and get id
        run_id = db.register_run(self._db_con, time.time(), description, 'running', environment)

        # call all the procedures
        for procedure in procedures:
            start_time = time.time()
            result = self.call_procedure(procedure['procedure_name'], kwargs=procedure['kwargs'])
            end_time = time.time()
            # register the procedure and result

        # update the run in the database to record its completion
        db.update_run_status(self._db_con, run_id, 'complete')

    def call_procedure(self, name, kwargs):
        """ call a procedure, all arguments must be passed as kwargs
        """
        return self._procedures[name]['fn'](**kwargs)
