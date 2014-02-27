import json
from flask import Flask, request, abort

import database as db
import run_manager as runm

app = Flask(__name__, static_folder='site')
sl = None


@app.route('/api')
def api_home():
    return "simpyl!"


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/newrun')
def new_run():
    return app.send_static_file('new_run.html')


@app.route('/runs')
def runs():
    return app.send_static_file('runs.html')


@app.route('/api/proc_inits')
def api_proc_inits():
    return json.dumps({'proc_inits': sl._proc_inits})


@app.route('/api/envs')
def api_envs():
    return json.dumps({'environment_names': [e['name'] for e in db.get_environments()]})


@app.route('/api/newenv', methods=['POST'])
def api_new_envs():
    if not request.json or not 'environment_name' in request.json:
        abort(400)
    db.register_environment(request.json['environment_name'])
    return json.dumps({'environment_name': request.json['environment_name']}), 201


@app.route('/api/runs/')
def api_get_runs():
    return json.dumps({'run_results': [r for r in db.get_run_results()]})


@app.route('/api/run/<int:run_id>')
def api_get_run(run_id):
    return json.dumps({'run_result': db.get_single_run_result(run_id)[0]})


@app.route('/api/newrun', methods=['POST'])
def api_new_run():
    if not request.json or not all([k in request.json for k in [
        'description', 'environment_name', 'proc_inits']]):
        abort(400)
    return json.dumps(runm.run(sl, request.json)), 201


@app.route('/api/log/<int:run_id>')
def get_log(run_id):
    return json.dumps({'log': runm.get_log(run_id)})


def run_server(simpyl_object):
    global sl
    sl = simpyl_object
    app.run(debug=True)
