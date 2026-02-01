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
    # Tips for making it CPU intensive:
    # - Check for prime numbers (loop from 2 to sqrt(n))
    # - Use hashlib.sha256() to hash data repeatedly
    # - Do math operations like sin(), cos(), pow()
    # - Use time.time() to check if duration has elapsed
    #
    # Example structure:
    #   end_time = time.time() + duration
    #   while time.time() < end_time:
    #       # do CPU intensive work here
    pass

@app.route('/work', methods=['POST'])
def work():
    # TODO: Get 'complexity' from JSON body (default to DEFAULT_COMPLEXITY)
    # TODO: Call burn_cpu() with the complexity value
    # TODO: Return JSON with "worker_id" (hostname) and "result"
    pass

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), HTTP_STATUS_OK

if __name__ == '__main__':
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    app.run(host='0.0.0.0', port=port)
