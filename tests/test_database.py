import unittest
import database as db


class TestDatabaseInit(unittest.TestCase):
    def setUp(self):
        db.reset_database('test.db')

    def test_reset(self):
        # check that all the tables exist and that they are empty, except for environment
        proc_results = db.get_proc_results()
        runs = db.get_runs()
        cachefilenames = db.get_cache_filenames()
        environments = db.get_environments()

        self.assertEqual(proc_results, [])
        self.assertEqual(runs, [])
        self.assertEqual(cachefilenames, [])
        self.assertEqual(environments, [{'name': 'default'}])


class TestDatabaseInsert(unittest.TestCase):
    def setUp(self):
        db.reset_database('test.db')
        self.run_result = {'id': None,
                           'timestamp_start': 12345,
                           'timestamp_stop': None,
                           'status': 'running',
                           'description': 'test_run',
                           'environment_name': 'default',
                           'proc_results': [
                               {'id': None,
                                'proc_name': 'foo',
                                'run_order': 0,
                                'timestamp_start': 12345,
                                'timestamp_stop': 12346,
                                'result': '42',
                                'run_id': None,
                                'arguments': [
                                    {'name': 'a', 'value': '2', 'from_cache': False},
                                    {'name': 'b', 'value': '3', 'from_cache': False}
                                ]},
                               {'id': None,
                                'proc_name': 'bar',
                                'run_order': 0,
                                'timestamp_start': 12346,
                                'timestamp_stop': 12400,
                                'result': '123',
                                'run_id': None,
                                'arguments': [
                                    {'name': 'aa', 'value': '20', 'from_cache': False},
                                    {'name': 'bb', 'value': '30', 'from_cache': False}
                                ]}
                           ]}

    def test_register_run_result(self):
        run_id = db.register_run_result(self.run_result)

        # check it was inserted properly
        self.assertIsNotNone(run_id)

        # update info and try to insert again
        self.run_result['id'] = run_id
        run_id = db.register_run_result(self.run_result)
        self.assertIsNone(run_id)

        # check the correct number of runs
        runs = db.get_runs()
        print(runs)
        self.assertEqual(len(runs), 1)

    def test_update_run_result(self):
        run_id = db.register_run_result(self.run_result)
        self.run_result['id'] = run_id
        self.run_result['timestamp_stop'] = 12400
        self.run_result['status'] = 'complete'

        db.update_run_result(self.run_result)

        # get rid of the proc_results and check the database stored the entry correctly
        self.run_result.pop('proc_results', None)
        run_results = db.get_run(self.run_result['id'])
        self.assertEqual(run_results[0], self.run_result)


if __name__ == '__main__':
    unittest.main()