import inspect

class Simpyl(object):
    def __init__(self, name):
        self._name = name
        self._procedures = {}

    def add_procedure(self, name):
        def decorator(fn):
            self._procedures[name] = {'fn': fn, 'details':inspect.getargspec(fn)}
            return fn
        return decorator

    def list_procedures(self):
        return self._procedures

    def run_procedure(self, name, args=None, kwargs={}):
        print args
        print("running {}".format(name))
        return self._procedures[name]['fn'](*args, **kwargs)
