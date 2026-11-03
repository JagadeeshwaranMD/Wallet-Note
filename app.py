"""
Wallet Note — Fullstack Python Application
Connected with Zoho Catalyst Data Store
"""

import os
from flask import Flask, send_from_directory
from backend.routes_api import api_bp

CLIENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client")

app = Flask(__name__, static_folder=CLIENT_DIR)

# Register REST API
app.register_blueprint(api_bp)

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response

# Serve Client Static Assets
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_client(path):
    if path != "" and os.path.exists(os.path.join(CLIENT_DIR, path)):
        return send_from_directory(CLIENT_DIR, path)
    return send_from_directory(CLIENT_DIR, "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT", 9000))
    print(f"Starting Wallet Note application on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

