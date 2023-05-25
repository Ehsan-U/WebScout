from flask import Flask, request, jsonify
import exceptions
from werkzeug.exceptions import HTTPException
from middlewares import before_request, after_request
from router import routes



app = Flask(__name__)
app.register_error_handler(HTTPException, exceptions.handle_error)
app.before_request(before_request)
app.after_request(after_request)
app.register_blueprint(routes)


app.run(host='0.0.0.0', port=5000, debug=True)