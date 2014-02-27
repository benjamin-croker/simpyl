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
    def test_envs(self):
        envs = json.loads(api_get('/envs'))
        self.assertEqual(envs, {'environment_names': ['default']})

    def test_newenv(self):
        # post a new environmnet
        post_data = api_post('/newenv', {'environment_name': 'test_env'})
        self.assertEqual(json.loads(post_data), {'environment_name': 'test_env'})

        # list all the environments
        envs = json.loads(api_get('/envs'))
        self.assertEqual(envs, {'environment_names': ['default', 'test_env']})


class TestProcInits(TestAPIBaseSetup):
    def test_proc_inits(self):
        proc_inits = {'proc_inits': [
            {'proc_name': 'trainer', 'run_order': None, 'arguments': [
                {'name': 'n_estimators', 'value': None},
                {'name': 'min_samples_split', 'value': None}],
             'arguments_str': ''}]}

        self.assertEqual(json.loads(api_get('/proc_inits')), proc_inits)


class TestRuns(TestAPIBaseSetup):
    def setUp(self):
        super(TestRuns, self).setUp()
        # get the results from manually running everything
        self.arguments = [
            [{'name': 'n_estimators', 'value': 10},
             {'name': 'min_samples_split', 'value': 2}],
            [{'name': 'n_estimators', 'value': 1},
             {'name': 'min_samples_split', 'value': 20}]
        ]
        self.arguments_str = [
            'n_estimators:10, min_samples_split:2',
            'n_estimators:1, min_samples_split:20'
        ]
        self.clfs, self.scores = zip(*[
            test_sim.main_trainer(n_estimators=10, min_samples_split=2),
            test_sim.main_trainer(n_estimators=1, min_samples_split=20)
        ])

        # get the proc inits and set the arguments
        self.proc_inits = json.loads(api_get('/proc_inits'))['proc_inits']

        # run the proc inits in order
        for i, proc_init in enumerate(self.proc_inits):
            proc_init['run_order'] = i

    def test_newrun(self):

        # set the arguments
        self.proc_inits[0]['arguments'] = self.arguments[0]
        self.proc_inits[0]['arguments_str'] = self.arguments_str[0]

        # create the run and run it
        run_init = {'description': "A test run",
                    'environment_name': 'default',
                    'proc_inits': self.proc_inits}

        run_result = json.loads(api_post('/newrun', run_init))

        # check some facts about the run result
        self.assertGreater(run_result['timestamp_stop'], run_result['timestamp_start'])
        self.assertEqual(
            run_result['proc_results'][0]['result'],
            str((self.clfs[0], self.scores[0]))
        )

    def test_runs(self):
        """ run two runs with different arguments and see if they are recalled
        """

        for i in xrange(len(self.arguments)):
            self.proc_inits[0]['arguments'] = self.arguments[i]
            self.proc_inits[0]['arguments_str'] = self.arguments_str[i]

            # create the run and run it
            run_init = {'description': "A test run {}".format(i),
                        'environment_name': 'default',
                        'proc_inits': self.proc_inits}
            api_post('/newrun', run_init)

        # get all the runs
        runs = json.loads(api_get('/runs'))['run_results']

        # check they are what we expect
        self.assertEqual(len(runs), len(self.arguments))
        for i in xrange(len(self.arguments)):
            self.assertEqual(
                runs[i]['proc_results'][0]['result'],
                str((self.clfs[i], self.scores[i]))
            )

        # check each run individually
        for run in runs:
            run_from_api = json.loads(api_get('/run/{}'.format(run['id'])))['run_result']
            self.assertEqual(run_from_api, run)
