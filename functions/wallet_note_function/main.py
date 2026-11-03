import logging
from flask import Request, Response, Flask
from backend.routes_api import api_bp

app = Flask(__name__)
app.register_blueprint(api_bp)

def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return resp

@app.after_request
def after_req(response):
    return add_cors(response)

def handler(request: Request):
    """Catalyst Advanced I/O function handler for Wallet Note."""
    if request.method == 'OPTIONS':
        return add_cors(Response('', status=200))

    environ = dict(request.environ)
    path_info = environ.get('PATH_INFO', '')
    prefix = '/server/wallet_note_function'
    if path_info.startswith(prefix):
        environ['PATH_INFO'] = path_info[len(prefix):] or '/'
        environ['SCRIPT_NAME'] = prefix

    # Support method override for cross-origin environments (e.g. Slate)
    override = request.args.get('_method')
    if override:
        environ['REQUEST_METHOD'] = override.upper()

    # Allow JSON parsing even if sent with text/plain to bypass CORS preflight
    ct = environ.get('CONTENT_TYPE', '')
    if not ct or 'text/plain' in ct:
        environ['CONTENT_TYPE'] = 'application/json'

    try:
        with app.request_context(environ):
            resp = app.full_dispatch_request()
            return add_cors(resp)
    except Exception as e:
        logging.error(f"Error handling request: {e}")
        return add_cors(Response(f"Internal Server Error: {e}", status=500))
