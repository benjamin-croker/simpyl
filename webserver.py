import json
from flask import Flask

app = Flask(__name__)
sl = None

@app.route('/')
def index():
    return "Hello World!"


@app.route('/api/procedures')
def get_procedures():
    print sl._proc_call_inits
    return json.dumps(sl._proc_call_inits)


def run_server(simpyl_object):
    global sl
    sl = simpyl_object
    app.run(debug=True)
