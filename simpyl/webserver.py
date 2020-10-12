from flask import Flask, request, abort, send_file, url_for, jsonify
import json
import os
import mimetypes

from simpyl import Simpyl

app = Flask(__name__, static_folder='site')
sl = Simpyl()


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


@app.route('/rundetail')
def run_detail():
    return app.send_static_file('run_detail.html')


@app.route('/api/proc_inits')
def api_proc_inits():
    return json.dumps({'proc_inits': sl.get_proc_inits()})


def use_environment():
    # TODO: implement API for creating a new environment
    pass


@app.route('/api/runs/')
def api_get_runs():
    return jsonify(
        {'run_results': [r for r in sl.get_run_results()]}
    )


@app.route('/api/run/<int:run_result_id>')
def api_get_run(run_result_id: int):
    return jsonify(
        {'run_result': sl.get_single_run_result(run_result_id)}
    )


@app.route('/api/newrun', methods=['POST'])
def api_new_run():
    if not request.json or not all(
            [k in request.json for k in
             ['description', 'proc_inits']]):
        abort(400)
    # add the environment
    run_init = request.json
    run_init['environment'] = sl.get_environment()
    run_result = sl.queue_run_init(run_init, convert_args_to_numbers=True)
    return json.dumps(run_result), 201


@app.route('/api/log/<int:run_result_id>')
def get_log(run_result_id: int):
    return json.dumps({'log': sl.get_log(run_result_id)})


@app.route('/api/figures/<int:run_result_id>')
def api_get_figures(run_result_id: int):
    figure_urls = [
        url_for(
            'api_get_figure', run_result_id=run_result_id, figure_name=fname, _external=True
        )
        for fname in sl.get_figures(run_result_id)
    ]
    return json.dumps({'figures': figure_urls})


@app.route('/api/figure/<int:run_result_id>/<string:figure_name>')
def api_get_figure(run_result_id: int, figure_name: str):
    img = sl.get_figure(run_result_id, figure_name)
    with open(os.path.join(app.root_path, 'temp.image'), 'wb') as tmp:
        tmp.write(img.read())
    img.close()
    return send_file('temp.image', mimetype=mimetypes.guess_type(figure_name)[0])


def run_server(simpyl_object: Simpyl):
    global sl
    sl = simpyl_object
    sl.start_queue()
    app.run(debug=False)
