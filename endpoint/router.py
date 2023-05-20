from flask import Blueprint, jsonify, request, abort
import utils
import validators


routes = Blueprint("routes", __name__)


@routes.route("/crawl", methods=['POST'])
def crawl():
    url = request.get_json().get("url")
    if url and validators.url(url):
        response = utils.process_route(request, route='crawl')
        return jsonify(response)
    abort(400)


@routes.route("/stats", methods=['POST'])
def stats():
    response = utils.process_route(request, route='stats')
    return jsonify(response)


@routes.route("/detail", methods=['POST'])
def detail():
    job_id = request.get_json().get("job_id")
    if job_id:
        response = utils.process_route(request, route='detail')
        return jsonify(response)
    abort(400)


@routes.route("/reset", methods=['POST'])
def reset():
    job_id = request.get_json().get("job_id")
    if job_id:
        response = utils.process_route(request, route='reset')
        return jsonify(response)
    abort(400)
