import json
from flask import Flask, request, abort

import database as db
import run_manager as runm

app = Flask(__name__)
sl = None


@app.route('/api')
def index():
    return "simpyl!"


@app.route('/api/proc_inits')
def get_procedures():
    return json.dumps(sl.get_proc_inits())


@app.route('/api/envs')
def get_environments():
    return json.dumps({'environment_names': [e['name'] for e in db.get_environments()]})


@app.route('/api/newenv', methods=['POST'])
def new_environment():
    if not request.json or not 'environment_name' in request.json:
        abort(400)
    db.register_environment(request.json['environment_name'])
    return json.dumps({'environment_name': request.json['environment_name']}), 201


@app.route('/api/runs/<env>')
def get_runs(env):
    return json.dumps({'run_results': [r for r in db.get_run_results(env)]})


@app.route('/api/run/<int:run_id>')
def get_run(run_id):
    return json.dumps({'run_result': db.get_single_run_result(run_id)})


@app.route('/api/newrun', methods=['POST'])
@app.route('/api/newrun', methods=['POST'])
def new_run():
    if not request.json or not all([k in request.json for k in [
            'description', 'environment_name', 'proc_call_inits']]):
        abort(400)
    runm.run(sl, request.json)


@app.route('/api/log/<env>/<int:run_id>')
def get_log(env, run_id):
    return json.dumps({'log': runm.get_log(env, run_id)})


def run_server(simpyl_object):
    global sl
    sl = simpyl_object
    app.run(debug=True)
