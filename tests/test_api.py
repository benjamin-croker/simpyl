import unittest
import urllib2
import json

import database as db
import test_sim

FLASK_URL = 'http://127.0.0.1:5000/api{}'


def api_get(url):
    return urllib2.urlopen(FLASK_URL.format(url)).read()


def api_post(url, data):
    req = urllib2.Request(FLASK_URL.format(url))
    req.add_header('Content-Type', 'application/json')
    return urllib2.urlopen(req, json.dumps(data)).read()


class TestAPIBaseSetup(unittest.TestCase):
    """ resets the database before each call
    """

    def setUp(self):
        db.reset_database('test.db')


class TestRunning(TestAPIBaseSetup):
    """ tests that the server is running
    """

    def test_running(self):
        self.assertEqual(api_get(''), 'simpyl!')


class TestEnvCalls(TestAPIBaseSetup):
    def test_get_envs(self):
        envs = json.loads(api_get('/envs'))
        self.assertEqual(envs, {'environment_names': ['default']})

    def test_post_envs(self):
        # post a new environmnet
        post_data = api_post('/newenv', {'environment_name': 'test_env'})
        self.assertEqual(json.loads(post_data), {'environment_name': 'test_env'})

        # list all the environments
        envs = json.loads(api_get('/envs'))
        self.assertEqual(envs, {'environment_names': ['default', 'test_env']})


class TestProcInits(TestAPIBaseSetup):
    def test_get_proc_inits(self):
        proc_inits = [{'proc_name': 'trainer', 'run_order': None, 'arguments': [
                          {'name': 'n_estimators', 'value': None},
                          {'name': 'min_samples_split', 'value': None}]}]

        self.assertEqual(json.loads(api_get('/proc_inits')), proc_inits)


class TestRuns(TestAPIBaseSetup):
    def test_post_run(self):
        # get the results from manually running everything
        clf, score = test_sim.main_trainer(n_estimators=10, min_samples_split=2)

        # get the proc inits and set the arguments
        proc_inits = json.loads(api_get('/proc_inits'))

        # the proc inits are already in the correct order
        for i, proc_init in enumerate(proc_inits):
            proc_init['run_order'] = i

        # set the arguments
        proc_inits[0]['arguments'] = [{'name': 'n_estimators', 'value': 10},
                                      {'name': 'min_samples_split', 'value': 2}]

        # create the run and run it
        run_init = {'description': "A test run",
                    'environment_name': 'default',
                    'proc_inits': proc_inits}

        run_result = json.loads(api_post('/newrun', run_init))

        # check some facts about the run result
        self.assertGreater(run_result['timestamp_stop'], run_result['timestamp_start'])
        self.assertEqual(run_result['proc_results'][0]['result'], str((clf, score)))



