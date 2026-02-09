# AUTHOR: Gilad Bitton
# RedID: 130621085

import time
import math
import os
import socket
import hashlib
from flask import Flask, jsonify, request

# Configuration
DEFAULT_PORT = 5000
DEFAULT_COMPLEXITY = 0.5  # Default seconds to burn CPU

HTTP_STATUS_OK = 200      # Status code ok

app = Flask(__name__)

# Function to burn CPU for a specified duration
def burn_cpu(duration=0.1):
    # Calculate the end time based on current time and duration
    end_time = time.time() + duration
    iterations = 0
    # Loop until the specified duration has passed
    while time.time() < end_time:
        # CPU intensive work: calculating prime numbers
        n = 10000
        # loops from 2 to sqrt(n), the possible factors of n
        for i in range(2, int(math.sqrt(n)) + 1):
            iterations += 1
            if n % i == 0:
                break 
    return iterations
        

    

# Endpoint to handle work requests
@app.route('/work', methods=['POST'])
def work():
    # Get 'complexity' from JSON body (default to DEFAULT_COMPLEXITY)
    payload = request.get_json(silent=True) or {}
    complexity = payload.get("complexity", DEFAULT_COMPLEXITY)
    # Call burn_cpu() with the complexity value
    iterations = burn_cpu(complexity)
    # Return JSON with "worker_id" (hostname) and "result"
    hostname = socket.gethostname()
    return jsonify({
        "worker_id": hostname, 
        "result": iterations
    }), HTTP_STATUS_OK

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), HTTP_STATUS_OK

if __name__ == '__main__':
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    app.run(host='0.0.0.0', port=port)
