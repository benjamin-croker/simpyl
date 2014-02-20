import unittest
import urllib2
import json

import database as db

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
        proc_inits = [{'proc_name': 'load', 'arguments': []},
                      {'proc_name': 'train', 'arguments': [
                          {'name': 'X_train', 'value': None},
                          {'name': 'y_train', 'value': None},
                          {'name': 'n_estimators', 'value': 10},
                          {'name': 'min_samples_split', 'value': 2}]},
                      {'proc_name': 'test', 'arguments': [
                          {'name': 'clf', 'value': None},
                          {'name': 'X', 'value': None},
                          {'name': 'y_true', 'value': None}]}]

        self.assertEqual(json.loads(api_get('/proc_inits')), proc_inits)



