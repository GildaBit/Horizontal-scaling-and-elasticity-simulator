import requests
import time
import threading
import sys

# Configuration
LB_HOST = "localhost"
LB_PORT = 8080
LB_URL = f"http://{LB_HOST}:{LB_PORT}/work"
REQUEST_TIMEOUT_SECONDS = 10

# Load test profiles - adjust as needed
LOW_LOAD_DURATION = 30       # seconds
LOW_LOAD_RPS = 1             # requests per second
LOW_LOAD_COMPLEXITY = 0.1    # seconds per request

HIGH_LOAD_DURATION = 60
HIGH_LOAD_RPS = 5
HIGH_LOAD_COMPLEXITY = 0.5

SPIKY_LOAD_DURATION = 20
SPIKY_LOAD_RPS = 15
SPIKY_LOAD_COMPLEXITY = 0.6

def send_request(complexity):
    try:
        requests.post(LB_URL, json={"complexity": complexity}, timeout=REQUEST_TIMEOUT_SECONDS)
    except Exception as e:
        print(f"Request failed: {e}")

def run_load(duration, rps, complexity):
    print(f"Starting load test: {duration}s, {rps} RPS, complexity={complexity}s")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        for _ in range(rps):
            threading.Thread(target=send_request, args=(complexity,)).start()
        time.sleep(1)

if __name__ == "__main__":
    # Feel free to modify this for your testing
    if len(sys.argv) < 2:
        print("Usage: python3 test_load.py [low|high|spiky]")
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == "low":
        run_load(LOW_LOAD_DURATION, LOW_LOAD_RPS, LOW_LOAD_COMPLEXITY)
    elif mode == "high":
        run_load(HIGH_LOAD_DURATION, HIGH_LOAD_RPS, HIGH_LOAD_COMPLEXITY)
    elif mode == "spiky":
        run_load(SPIKY_LOAD_DURATION, SPIKY_LOAD_RPS, SPIKY_LOAD_COMPLEXITY)
    else:
        print("Unknown mode. Use 'low' or 'high' or 'spiky'")

