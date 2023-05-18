from flask import Flask, request, jsonify
import exceptions
from werkzeug.exceptions import HTTPException
from middlewares import before_request, after_request
import utils



app = Flask(__name__)
app.register_error_handler(HTTPException, exceptions.handle_error)
app.before_request(before_request)
app.after_request(after_request)


@app.route("/crawl", methods=['POST'])
def crawl():
    response = utils.process_route(request, route='crawl')
    return jsonify(response)


@app.route("/stats", methods=['POST'])
def stats():
    response = utils.process_route(request, route='stats')
    return jsonify(response)


@app.route("/detail", methods=['POST'])
def detail():
    response = utils.process_route(request, route='detail')
    return jsonify(response)


@app.route("/reset", methods=['POST'])
def reset():
    response = utils.process_route(request, route='reset')
    return jsonify(response)


app.run(debug=True)