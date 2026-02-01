import requests
import threading
from flask import Flask, request, jsonify

# Configuration
LB_PORT = 8080                    # Port the load balancer listens on
WORKER_TIMEOUT_SECONDS = 10       # Timeout for forwarding requests to workers

HTTP_STATUS_OK = 200              # Status code ok

app = Flask(__name__)

# TODO: Initialize a list of active ports
active_ports = []
# current port index
current_index = 0
# lock for concurrency
lock = threading.Lock()

@app.route('/register', methods=['POST'])
def register():
    # TODO: Add port from request body to active_ports list
    bad_request = jsonify({
            "status": "bad request",
        }), 400
    body = request.get_json(silent=True)
    if body is None:
        return bad_request
    if body.get('port') is None:
        return bad_request
    port = body.get('port')
    if not isinstance(port, int) or port <= 0 or port > 65535:
        return bad_request
    lock.acquire()
    try:
        if port in active_ports:
            return jsonify({
            "status": "already registered",
            "port": port
        }), 200
        active_ports.append(port)  
    finally:
        lock.release()
    return jsonify({
        "status": "registered",
        "port": port
    }), 200

@app.route('/deregister', methods=['POST'])
def deregister():
    # TODO: Remove port from request body from active_ports list
    pass

@app.route('/work', methods=['POST'])
def proxy_work():
    # TODO: Check if there are any active workers
    # TODO: Implement Round Robin selection of worker
    # TODO: Forward request to the selected worker (http://localhost:<port>/work)
    # TODO: Return the response from the worker
    # TODO: Handle connection errors (if worker is down)
    pass

@app.route('/health', methods=['GET'])
def health():
    # Optional: Return status and number of workers
    return jsonify({"status": "healthy"}), HTTP_STATUS_OK

if __name__ == '__main__':
    print(f"Load Balancer running on port {LB_PORT}")
    app.run(host='0.0.0.0', port=LB_PORT, threaded=True)
