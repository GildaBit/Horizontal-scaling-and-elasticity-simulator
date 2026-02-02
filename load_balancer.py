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
    global current_index
    # TODO: Remove port from request body from active_ports list
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
    removed = False
    try:
        if port in active_ports:
            active_ports.remove(port) 
            removed = True 
            if not active_ports:
                current_index = 0
            else:
                current_index %= len(active_ports)             
    finally:
        lock.release()
    if removed:
        return jsonify({
            "status": "removed",
            "port": port
        }), 200
    else:
        return jsonify({
            "status": "unregistered",
            "port": port
        }), 200


@app.route('/work', methods=['POST'])
def proxy_work():
    # TODO: Check if there are any active workers
    global current_index
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    lock.acquire()
    try:
        num_workers = len(active_ports)
    finally:
        lock.release()
    if num_workers == 0:
        return jsonify({
            "status": "Service unavailable",
        }), 503
    for i in range(num_workers):
        lock.acquire()
        try:
            if current_index >= len(active_ports) or current_index < 0:
                current_index = 0
            if not active_ports:
                return jsonify({
                    "status": "Service unavailable",
                }), 503
            port = active_ports[current_index]
            current_index = (current_index + 1) % len(active_ports)
        finally:
            lock.release()
        # TODO: Implement Round Robin selection of worker
        # TODO: Forward request to the selected worker (http://localhost:<port>/work)
        url = f"http://localhost:{port}/work"
        # TODO: Return the response from the worker
        try:
            response = requests.post(url, json=body, timeout=WORKER_TIMEOUT_SECONDS) # posts a request
            return jsonify(response.json()), response.status_code
        # In case of non json response
        except ValueError:
            return response.text, response.status_code
        # In case of a worker being down
        except requests.exceptions.RequestException as e:
            lock.acquire()
            try:
                if port in active_ports:
                    active_ports.remove(port)
                    if active_ports:
                        current_index %= len(active_ports)
                    else:
                        current_index = 0
            finally:
                lock.release()
        
    return jsonify({
        "status": "Bad gateway"
    }), 502

@app.route('/health', methods=['GET'])
def health():
    # Optional: Return status and number of workers
    return jsonify({"status": "healthy"}), HTTP_STATUS_OK

if __name__ == '__main__':
    print(f"Load Balancer running on port {LB_PORT}")
    app.run(host='0.0.0.0', port=LB_PORT, threaded=True)
