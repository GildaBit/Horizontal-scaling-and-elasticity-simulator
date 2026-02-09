# AUTHOR: Gilad Bitton
# RedID: 130621085

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
COOLDOWN_PERIOD = 10          # seconds between scaling actions
CHECK_INTERVAL = 5            # seconds between health checks

# Worker configuration
CONTAINER_PORT = 5000         # Port Flask runs on inside container
WORKER_START_PORT = 5001      # First host port for workers

# Initialize Docker client
client = docker.from_env()
active_containers = {}  # port -> container

# function to start a worker container on a specific port
def start_worker(port):
    # try to start container from IMAGE_NAME on host port 'port'
    try:
        container = client.containers.run(
            IMAGE_NAME,
            detach=True,
            ports={f'{CONTAINER_PORT}/tcp': port}, 
        )
    except docker.errors.DockerException as e:
        return False 
    
    # Wait for the worker to become healthy and reachable, grace period of 5 seconds
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
        # Never became reachable, clean up and return False
        try:
            container.stop()
            container.remove()
        except docker.errors.DockerException:
            pass
        return False

    # post an HTTP request to Load Balancer to register this worker with its port    
    try:
        response = requests.post(
            f"{LB_URL}/register",
            json={"port": port},
            timeout=2
        )
    # Clean up on failure and return False
    except requests.exceptions.RequestException:
        try:
            container.stop()
            container.remove()
        except docker.errors.DockerException:
            pass
        return False

    # If registration succeeded, keep track of the container and return True
    if response.ok:
        active_containers[port] = container
        return True
    # Else, clean up and return False
    else:
        try:
            container.stop()
            container.remove()
        except docker.errors.DockerException:
            pass
        return False

# function to stop a worker container on a specific port
def stop_worker(port):
    # Get the container object from active_containers given the port to be removed
    container = active_containers.get(port)
    if container is None:
        return
    
    # Post an HTTP request to Load Balancer to deregister this worker
    try:
        response = requests.post(
            f"{LB_URL}/deregister",
            json={"port": port},
            timeout=2
        )
    except requests.exceptions.RequestException:
        pass

    # Stop and remove the container
    try:
        container.stop(timeout=5)
    except docker.errors.DockerException:
        pass
    try:
        container.remove(force=True)
    except docker.errors.DockerException:
        pass
    
    # Remove from active_containers
    active_containers.pop(port, None)

# Monitoring loop
def monitor():
    # Keep track of last scaling action time
    most_recent_scale = 0

    while (True):
        # Calculate average response time of Load Balancer over several samples
        samples = 5
        latencies = []
        failures = 0

        for _ in range(samples):
            t0 = time.perf_counter()
            try:
                r = requests.post(
                    f"{LB_URL}/work",
                    json={"complexity": 0.01},
                    timeout=1
                )
                latencies.append(time.perf_counter() - t0)
            except requests.exceptions.RequestException:
                failures += 1

        # If the LB is timing out, that's overload — treat it as "very high latency"
        if failures >= 2:
            avg = 999.0
        elif latencies:
            avg = sum(latencies) / len(latencies)
        else:
            avg = None

        # Check health of each worker container, if not healthy remove it from LB
        for port, container in list(active_containers.items()):
            try:
                container.reload()
                if container.status != "running":
                    # Tell LB to forget this worker
                    try:
                        requests.post(
                            f"{LB_URL}/deregister",
                            json={"port": port},
                            timeout=2
                        )
                    except requests.exceptions.RequestException:
                        pass  # LB might already have removed it

                    # Remove from active_containers
                    active_containers.pop(port, None)
            # If any Docker error occurs, assume container is gone/unreachable, remove from LB
            except docker.errors.DockerException:
                # Container is gone / unreachable
                try:
                    requests.post(
                        f"{LB_URL}/deregister",
                        json={"port": port},
                        timeout=2
                    )
                except requests.exceptions.RequestException:
                    pass

                active_containers.pop(port, None)

        # Print current status: average latency and number of workers
        num_workers = len(active_containers)
        if avg is None:
            print(
                f"[AUTOSCALER] avg_latency=N/A workers={num_workers} samples=0",
                flush=True
            )
        else:
            print(
                f"[AUTOSCALER] avg_latency={avg:.3f}s workers={num_workers} samples={len(latencies)}",
                flush=True
            )

        # Scaling logic
        now = time.time()
        # Wait until cooldown period has passed
        in_cooldown = (now - most_recent_scale) < COOLDOWN_PERIOD
        if not in_cooldown and avg is not None:
            # Check scale up condition
            if avg > SCALE_UP_THRESHOLD and num_workers < MAX_WORKERS:
                port = WORKER_START_PORT
                # Find the next available port
                while port in active_containers:
                    port += 1

                # If starting worker succeeded, update most_recent_scale
                if start_worker(port):
                    most_recent_scale = time.time()

            # Check scale down condition
            elif avg < SCALE_DOWN_THRESHOLD and num_workers > MIN_WORKERS:
                # Stop the worker with the highest port number
                port = max(active_containers.keys())
                stop_worker(port)
                # update most_recent_scale
                most_recent_scale = time.time()

        # Wait before next check    
        time.sleep(CHECK_INTERVAL)

# Main entry point
if __name__ == "__main__":
    # Build Docker image first
    try:
        print("Building Docker image...")
        client.images.build(
            path=".", # current directory
            tag=IMAGE_NAME,
            rm=True # remove intermediate containers
        )
        print("Docker image built successfully")
    # Handle build errors
    except docker.errors.BuildError as e:
        print("Docker image build failed:", e)
        exit(1)
    # Handle other Docker API errors
    except docker.errors.APIError as e:
        print("Docker API error:", e)
        exit(1)

    # Start initial worker
    start_worker(WORKER_START_PORT)
    # Start monitoring loop
    monitor()

