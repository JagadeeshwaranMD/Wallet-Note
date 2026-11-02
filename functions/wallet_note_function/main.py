import logging
from flask import Request, Response, Flask, make_response
from backend.routes_api import api_bp

app = Flask(__name__)
app.register_blueprint(api_bp)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response

def handler(request: Request):
    """Catalyst Advanced I/O function handler for Wallet Note."""
    if request.method == 'OPTIONS':
        resp = make_response('', 200)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        return resp

    environ = dict(request.environ)
    path_info = environ.get('PATH_INFO', '')
    prefix = '/server/wallet_note_function'
    if path_info.startswith(prefix):
        environ['PATH_INFO'] = path_info[len(prefix):] or '/'
        environ['SCRIPT_NAME'] = prefix

    try:
        with app.request_context(environ):
            return app.full_dispatch_request()
    except Exception as e:
        logging.error(f"Error handling request: {e}")
        return make_response(f"Internal Server Error: {e}", 500)
