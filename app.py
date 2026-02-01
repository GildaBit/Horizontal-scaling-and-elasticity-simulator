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

def burn_cpu(duration=0.1):
    # TODO: Implement a CPU-burning loop that runs for 'duration' seconds
    # 
    end_time = time.time() + duration
    iterations = 0
    while time.time() < end_time:
        # CPU intensive work: calculating prime numbers
        n = 10000
        # loops from 2 to sqrt(n), the possible factors of n
        for i in range(2, int(math.sqrt(n)) + 1):
            iterations += 1
            if n % i == 0:
                break 
    return iterations
        

    


@app.route('/work', methods=['POST'])
def work():
    # TODO: Get 'complexity' from JSON body (default to DEFAULT_COMPLEXITY)
    complexity = DEFAULT_COMPLEXITY
    if request.json.get('complexity') is not None:
        complexity = request.json.get('complexity')
    # TODO: Call burn_cpu() with the complexity value
    iterations = burn_cpu(complexity)
    # TODO: Return JSON with "worker_id" (hostname) and "result"
    hostname = socket.gethostname()
    return jsonify({
        "worker_id": hostname, 
        "result": iterations
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), HTTP_STATUS_OK

if __name__ == '__main__':
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    app.run(host='0.0.0.0', port=port)
