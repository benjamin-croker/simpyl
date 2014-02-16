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


if __name__ == '__main__':
    unittest.main()