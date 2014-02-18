from simpyl import Simpyl
import os
import database as db

# use the test database
db.reset_database(os.path.join('tests/test.db'))

sl = Simpyl()


@sl.add_procedure('foo')
def foo(a, b):
    """ adds two numbers
    """
    return a + b


@sl.add_procedure('bar')
def bar(x, y):
    """ multiplies two numbers
    """
    return x * y


sl.start()