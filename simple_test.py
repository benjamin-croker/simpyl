import os

from simpyl import Simpyl
import simpyl.database as db

sl = Simpyl()


@sl.add_procedure('foo')
def foo(a, b):
    return a + b


@sl.add_procedure('bar')
def bar(a, b):
    return a * b


if __name__ == '__main__':
    # use the test database
    db.reset_database(os.path.join('simpyl', 'tests', 'test.db'))
    sl.run([('foo', {'a': [1, 2, 3], 'b': [4, 5, 6]}),
            ('bar', {'a': 10, 'b': 20})],
           description="No expansion",
           expand_args='by_proc')
    sl.run([('foo', {'a': [1, 2, 3], 'b': [4, 5, 6]}),
            ('bar', {'a': [1, 2], 'b': [4, 5]})],
           description="By proc expansion",
           expand_args='by_proc')
    sl.run([('foo', {'a': [1, 2, 3], 'b': [4, 5, 6]}),
            ('bar', {'a': [1, 2, 3], 'b': [4, 5, 6]})],
           description="By run expansion, separating runs",
           expand_args='by_proc', separate_runs=True)

    sl.start()