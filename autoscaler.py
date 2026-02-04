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
    if container is None:
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
    
    active_containers.pop(port, None)

def monitor():
    # TODO: Infinite loop
    most_recent_scale = 0
    while (True):
        # 1. Calculate average response time of Load Balancer
        samples = 10
        latencies = []
        for _ in range(samples):
            benchmark = time.perf_counter() #time.time() but more precise
            try:
                request = requests.post(f"{LB_URL}/work", json={}, timeout=10)
                latencies.append(time.perf_counter() - benchmark)
            except requests.exceptions.RequestException:
                pass

        avg = None
        if latencies:
            avg = sum(latencies) / len(latencies)

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

                    active_containers.pop(port, None)

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


        now = time.time()
        in_cooldown = (now - most_recent_scale) < COOLDOWN_PERIOD
        if not in_cooldown and avg is not None:
            # 2. Check scale up condition
            if avg > SCALE_UP_THRESHOLD and num_workers < MAX_WORKERS:
                port = WORKER_START_PORT
                while port in active_containers:
                    port += 1

                if start_worker(port):
                    most_recent_scale = time.time()

            # 3. Check scale down condition
            elif avg < SCALE_DOWN_THRESHOLD and num_workers > MIN_WORKERS:
                port = max(active_containers.keys())
                stop_worker(port)
                most_recent_scale = time.time()
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # TODO: Build Docker image first
    try:
        print("Building Docker image...")
        client.images.build(
            path=".", # current directory
            tag=IMAGE_NAME,
            rm=True # remove intermediate containers
        )
        print("Docker image built successfully")
    except docker.errors.BuildError as e:
        print("Docker image build failed:", e)
        exit(1)
    except docker.errors.APIError as e:
        print("Docker API error:", e)
        exit(1)

    # TODO: Start initial worker
    start_worker(WORKER_START_PORT)
    # TODO: Start monitoring loop
    monitor()

