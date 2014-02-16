import unittest
import database as db


class TestDatabaseInit(unittest.TestCase):
    def setUp(self):
        db.reset_database('test.db')

    def test_reset(self):
        # check that all the tables exist and that they are empty, except for environment
        proc_results = db.get_proc_results()
        runs = db.get_run_results()
        cachefilenames = db.get_cache_filenames()
        environments = db.get_environments()

        self.assertEqual(proc_results, [])
        self.assertEqual(runs, [])
        self.assertEqual(cachefilenames, [])
        self.assertEqual(environments, [{'name': 'default'}])

class TestDatabaseBaseSetup(unittest.TestCase):

    def setUp(self):
        db.reset_database('test.db')
        # set some fake data to test with
        self.run_results = [{'id': None,
                           'timestamp_start': 12345.0,
                           'timestamp_stop': None,
                           'status': 'running',
                           'description': 'test_run',
                           'environment_name': 'default',
                           'proc_results': [
                               {'id': None,
                                'proc_name': 'foo',
                                'run_order': 0,
                                'timestamp_start': 12345.0,
                                'timestamp_stop': 12346.0,
                                'result': '42',
                                'run_result_id': None,
                                'arguments': [
                                    {'name': 'a', 'value': '2', 'from_cache': False},
                                    {'name': 'b', 'value': '3', 'from_cache': False}
                                ]},
                               {'id': None,
                                'proc_name': 'bar',
                                'run_order': 1,
                                'timestamp_start': 12346.0,
                                'timestamp_stop': 12400.0,
                                'result': '123',
                                'run_result_id': None,
                                'arguments': [
                                    {'name': 'aa', 'value': '20', 'from_cache': False},
                                    {'name': 'bb', 'value': '30', 'from_cache': False}
                                ]}
                           ]},
                            {'id': None,
                           'timestamp_start': 11111,
                           'timestamp_stop': None,
                           'status': 'running',
                           'description': 'test_run',
                           'environment_name': 'default',
                           'proc_results': [
                               {'id': None,
                                'proc_name': 'foo',
                                'run_order': 0,
                                'timestamp_start': 11111.0,
                                'timestamp_stop': 11112.0,
                                'result': '42',
                                'run_result_id': None,
                                'arguments': [
                                    {'name': 'a', 'value': '2', 'from_cache': False},
                                    {'name': 'b', 'value': '3', 'from_cache': False}
                                ]},
                               {'id': None,
                                'proc_name': 'bar',
                                'run_order': 1,
                                'timestamp_start': 11112.0,
                                'timestamp_stop': 22222.0,
                                'result': '123',
                                'run_result_id': None,
                                'arguments': [
                                    {'name': 'aa', 'value': '20', 'from_cache': False},
                                    {'name': 'bb', 'value': '30', 'from_cache': False}
                                ]}
                           ]}]


class TestDatabaseEnvironment(TestDatabaseBaseSetup):
    def test_register_environment(self):
        """ Test an environment can be added to the database and read back
        """
        # the default should already exist
        environments = db.get_environments()
        self.assertEqual(environments, [{'name': 'default'}])

        # add a new one
        db.register_environment('newenv')
        environments = db.get_environments()
        self.assertEqual(environments, [{'name': 'default'}, {'name': 'newenv'}])



class TestDatabaseRunResult(TestDatabaseBaseSetup):
    def test_register_run_result(self):
        """ Test that a run result can be inserted into the database
        """
        run_id = db.register_run_result(self.run_results[0])
        self.assertIsNotNone(run_id)

        # update info and try to insert again
        self.run_results[0]['id'] = run_id
        run_id = db.register_run_result(self.run_results[0])
        self.assertIsNone(run_id)

        # check the correct number of runs
        runs = db.get_run_results()
        self.assertEqual(len(runs), 1)

        #insert another run
        run_id = db.register_run_result(self.run_results[1])
        self.assertIsNotNone(run_id)

        # check the correct number of runs
        runs = db.get_run_results()
        self.assertEqual(len(runs), 2)

    def test_update_run_result(self):
        """ Test a run result can be updated
        """
        run_id = db.register_run_result(self.run_results[0])
        self.run_results[0]['id'] = run_id
        self.run_results[0]['timestamp_stop'] = 12400
        self.run_results[0]['status'] = 'complete'

        db.update_run_result(self.run_results[0])

        # get rid of the proc_results and check the database stored the entry correctly
        self.run_results[0].pop('proc_results', None)
        run_results = db.get_single_run_result(self.run_results[0]['id'])
        self.assertEqual(run_results[0], self.run_results[0])

    def test_get_run_results(self):
        """ check the correct runs are returned for the specified environments
        """
        for run in self.run_results:
            run_id = db.register_run_result(run)
            run['id'] = run_id

        runs = db.get_run_results('default')
        self.assertEqual(len(runs), 2)
        runs = db.get_run_results('does_not_exists')
        self.assertEqual(len(runs), 0)


class TestDatabaseProcResult(TestDatabaseBaseSetup):
    def test_register_proc_result(self):
        """ Test a procedure call can be inserted into the database
        """
        # check insert a procedure result
        proc_id = db.register_proc_result(self.run_results[0]['proc_results'][0])
        self.assertIsNotNone(proc_id)
        self.run_results[0]['proc_results'][0]['id'] = proc_id

        # try to insert it again
        proc_id = db.register_proc_result(self.run_results[0]['proc_results'][0])
        self.assertIsNone(proc_id)

        # check the correct number of procs
        procs = db.get_proc_results()
        self.assertEqual(len(procs), 1)

        #insert another run
        proc_id = db.register_proc_result(self.run_results[0]['proc_results'][1])
        self.assertIsNotNone(proc_id)

        # check the correct number of runs
        procs = db.get_proc_results()
        self.assertEqual(len(procs), 2)

    def test_get_proc_results(self):
        """ Test a procedure call can be read back correctly
        """
        # insert runs and procedures
        for run in self.run_results:
            run_id = db.register_run_result(run)
            run['id'] = run_id

            for proc in run['proc_results']:
                proc['run_result_id'] = run_id
                proc_id = db.register_proc_result(proc)
                proc['id'] = proc_id

        # check the two procedures were registered for each run
        procs = db.get_proc_results(self.run_results[0]['id'])
        self.assertEqual(procs, self.run_results[0]['proc_results'])


if __name__ == '__main__':
    unittest.main()