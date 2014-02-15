import json
import os
from flask import Flask, request, abort

import run_manager as runm

app = Flask(__name__)
sl = None

@app.route('/')
def index():
    return "simpyl!"


@app.route('/api/procedures')
def get_procedures():
    return json.dumps(sl.proc_call_inits)


@app.route('/api/envs')
def list_environments():
    return json.dumps(runm.get_environments())


@app.route('/api/newenv', methods=['POST'])
def new_environment():
    print request.json
    if not request.json or not 'name' in request.json:
        abort(400)
    runm.create_environment(request.json['name'])
    return json.dumps({'name': request.json['name']}), 201


def run_server(simpyl_object):
    global sl
    sl = simpyl_object
    app.run(debug=True)
