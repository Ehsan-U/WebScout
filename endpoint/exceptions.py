from flask import jsonify, json


def handle_error(error):
    response = error.get_response()
    response.data = json.dumps({
        "code": error.code,
        "description": error.description,
    })
    response.content_type = "application/json"
    return response