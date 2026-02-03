import docker
import requests
import time

# Important: Do NOT change the names (with upper case) of 
# all the constants defined at the beginning. 

# Configuration
IMAGE_NAME = "worker-app:latest"
LB_HOST = "localhost"
LB_PORT = 8080
LB_URL = f"http://{LB_HOST}:{LB_PORT}"

# Scaling thresholds - adjust these based on your testing

# VERY IMPORTANT: the numbers used below are only for example, experiment and use 
# the numbers specific to your run-time environment in your code
# as long as the scaling up and scaling down logic can be exercised 
# with your testing.

MIN_WORKERS = 1
MAX_WORKERS = 5
SCALE_UP_THRESHOLD = 1.0      # seconds - scale up if avg response > this
SCALE_DOWN_THRESHOLD = 0.5    # seconds - scale down if avg response < this
COOLDOWN_PERIOD = 15          # seconds between scaling actions
CHECK_INTERVAL = 5            # seconds between health checks

# Worker configuration
CONTAINER_PORT = 5000         # Port Flask runs on inside container
WORKER_START_PORT = 5001      # First host port for workers

# TODO: Initialize Docker client
client = docker.from_env()
active_containers = {}  # port -> container

def start_worker(port):
    # TODO: Use Docker client to run "worker-app" container on specific port
    try:
        container = client.containers.run(
            IMAGE_NAME,
            detach=True,
            ports={f'{CONTAINER_PORT}/tcp': port}, 
        )
    except docker.errors.DockerException as e:
        return False 
    # TODO: Register port with Load Balancer
    deadline = time.time() + 5  # wait up to 5 seconds
    worker_url = f"http://localhost:{port}/health"

    while time.time() < deadline:
        try:
            r = requests.get(worker_url, timeout=0.5)
            # Any HTTP response means the service is reachable
            break
        except requests.exceptions.RequestException:
            time.sleep(0.2)
    else:
        # Never became reachable
        try:
            container.stop()
            container.remove()
        except docker.errors.DockerException:
            pass
        return False
    try:
        response = requests.post(
            f"{LB_URL}/register",
            json={"port": port},
            timeout=2
        )
    except requests.exceptions.RequestException:
        try:
            container.stop()
            container.remove()
        except docker.errors.DockerException:
            pass
        return False
    if response.ok:
        active_containers[port] = container
        return True
    else:
        try:
            container.stop()
            container.remove()
        except docker.errors.DockerException:
            pass
        return False

def stop_worker(port):
    # TODO: Deregister from Load Balancer
    container = active_containers.get(port)
    if container is None
        return
    
    try:
        response = requests.post(
            f"{LB_URL}/deregister",
            json={"port": port},
            timeout=2
        )
    except requests.exceptions.RequestException:
        pass

    try:
        container.stop(timeout=5)
    except docker.errors.DockerException:
        pass
    
    try:
        container.remove(force=True)
    except docker.errors.DockerException:
        pass
    
    active_containers.remove(port, None)

def monitor():
    # TODO: Infinite loop
    while (True):
    # 1. Calculate average response time of Load Balancer
    # 2. Check scale up condition
    # 3. Check scale down condition
    # 4. Respect cooldown period
    pass

if __name__ == "__main__":
    # TODO: Build Docker image first
    # TODO: Start initial worker
    # TODO: Start monitoring loop
    pass
