# AUTHOR: Gilad Bitton
# RedID: 130621085

import requests
import threading
from flask import Flask, request, jsonify

# Configuration
LB_PORT = 8080                    # Port the load balancer listens on
WORKER_TIMEOUT_SECONDS = 10       # Timeout for forwarding requests to workers

HTTP_STATUS_OK = 200              # Status code ok

app = Flask(__name__)

# Initialize a list of active ports
active_ports = []
# current port index
current_index = 0
# lock for concurrency
lock = threading.Lock()

# Endpoint to register a worker
@app.route('/register', methods=['POST'])
def register():
    # Initialize a bad request response to return in case of errors
    bad_request = jsonify({
        "status": "bad request",
    }), 400
    # Get the json body from the request
    body = request.get_json(silent=True)
    if body is None:
        return bad_request
    # Ensure port is present and valid
    if body.get('port') is None:
        return bad_request
    port = body.get('port')
    if not isinstance(port, int) or port <= 0 or port > 65535:
        return bad_request
    
    # Add port to active_ports list if not already present
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

# Endpoint to deregister a worker
@app.route('/deregister', methods=['POST'])
def deregister():
    # make the current_index variable refer to the global one
    global current_index
    # Set a bad request response to return in case of errors
    bad_request = jsonify({
        "status": "bad request",
    }), 400
    # Get the json body from the request
    body = request.get_json(silent=True)
    # Ensure body and port are present and valid
    if body is None:
        return bad_request
    if body.get('port') is None:
        return bad_request
    port = body.get('port')
    if not isinstance(port, int) or port <= 0 or port > 65535:
        return bad_request

    # Remove port from active_ports list if present
    lock.acquire()
    removed = False
    try:
        if port in active_ports:
            active_ports.remove(port) 
            removed = True 
            # Adjust current_index if necessary
            if not active_ports:
                current_index = 0
            else:
                current_index %= len(active_ports)             
    finally:
        lock.release()
    # Return appropriate response
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

# function to forward /work requests to workers using Round Robin
@app.route('/work', methods=['POST'])
def proxy_work():
    # set the current_index variable to refer to the global one
    global current_index
    # Get the json body from the request
    body = request.get_json(silent=True)
    if body is None:
        body = {}

    # Check if there are active workers
    lock.acquire()
    try:
        num_workers = len(active_ports)
    finally:
        lock.release()
    
    # If no workers are available, return 503
    if num_workers == 0:
        return jsonify({
            "status": "Service unavailable",
        }), 503

    # Try to forward the request to workers in Round Robin fashion
    for i in range(num_workers):
        lock.acquire()
        try:
            # Ensure current_index is within bounds
            if current_index >= len(active_ports) or current_index < 0:
                current_index = 0
            if not active_ports:
                break 
            # Select the next worker port
            port = active_ports[current_index]
            # Update current_index for next request
            current_index = (current_index + 1) % len(active_ports)
        finally:
            lock.release()
        
        # Set the worker URL
        url = f"http://localhost:{port}/work"
        try:
            # Forward the request to the selected worker
            response = requests.post(url, json=body, timeout=WORKER_TIMEOUT_SECONDS)
            # In case of a json response, forward it
            return jsonify(response.json()), response.status_code
        # In case of non json response
        except ValueError:
            return response.text, response.status_code
        # In case of a worker being down
        except requests.exceptions.ConnectionError:
            print(f"Worker at {port} connection failed. Removing.")
            lock.acquire()
            try:
                # Remove the unresponsive port and adjust current_index
                if port in active_ports:
                    active_ports.remove(port)
                    if active_ports:
                        current_index %= len(active_ports)
                    else:
                        current_index = 0
            finally:
                lock.release()
            continue # keep trying other workers (resilience)
        except requests.exceptions.Timeout:
            continue # keep trying other workers (resilience)
    # If all workers failed, return 502
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
