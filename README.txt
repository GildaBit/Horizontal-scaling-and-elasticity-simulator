Author: Gilad Bitton
RedID: 130621085

AUTOSCALING LOAD-BALANCED WORKER SYSTEM

This project is a small prototype that demonstrates load balancing and autoscaling using Python, Flask, and Docker. It is intentionally simple and meant for learning and experimentation, not for production use.

The system runs multiple worker containers that perform CPU-intensive work. A load balancer distributes incoming requests across those workers, and an autoscaler monitors response times and decides when to add or remove workers.

ARCHITECTURE OVERVIEW

Clients or a load generator send requests to the load balancer. The load balancer forwards each request to one of the available workers using a round-robin strategy. Workers execute CPU-bound work and return a response. The autoscaler continuously measures latency through the load balancer and scales the number of workers up or down based on predefined thresholds.

COMPONENTS

Worker (app.py)

The worker is a Flask application that simulates real computation by burning CPU cycles for a configurable amount of time.

Endpoints:

* POST /work: performs CPU work controlled by a "complexity" value in seconds
* GET /health: basic health check

Each response includes the worker hostname so it is easy to see which worker handled a request.

Load Balancer (load_balancer.py)

The load balancer is a Flask application listening on port 8080. It keeps track of active worker ports and forwards requests using round-robin scheduling.

Key behavior:

* Workers register and deregister dynamically
* Requests are forwarded with a timeout
* Unresponsive workers are removed automatically

Endpoints:

* POST /register
* POST /deregister
* POST /work
* GET /health

Autoscaler (autoscaler.py)

The autoscaler builds the worker Docker image, starts worker containers, and decides when to scale.

It works by repeatedly:

1. Sending sample requests to the load balancer
2. Measuring average response latency
3. Scaling up when latency is too high
4. Scaling down when latency is consistently low

A cooldown period is used to prevent rapid oscillations.

Important configuration values include:

* MIN_WORKERS and MAX_WORKERS
* SCALE_UP_THRESHOLD and SCALE_DOWN_THRESHOLD
* COOLDOWN_PERIOD

These values are meant to be adjusted during testing.

Load Generator (test_load.py)

The load generator is a simple script used to stress the system and trigger scaling behavior. It supports three traffic patterns:

* low: light, steady traffic
* high: sustained heavy load
* spiky: short bursts of high traffic

Each request includes a complexity parameter that controls how much CPU work is performed by a worker.

REQUIREMENTS

* Python 3.8 or newer
* Docker (must be running)

Python dependencies are listed in requirements.txt:
flask
requests
docker

HOW TO RUN

1. Install dependencies:

pip install -r requirements.txt

2. Start the load balancer:

python load_balancer.py

The load balancer listens on port 8080.

3. Start the autoscaler (in a separate terminal):

python autoscaler.py

This builds the worker image, starts an initial worker, and begins monitoring and scaling.

4. Generate load (in another terminal):

python test_load.py low
python test_load.py high
python test_load.py spiky

You should see workers being added or removed as load changes.

