# -------- Configuration --------
IMAGE_NAME = worker-app:latest
PYTHON = python3

# -------- Targets --------

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make build        Build worker Docker image"
	@echo "  make lb           Run load balancer"
	@echo "  make autoscaler   Run autoscaler (builds image first)"
	@echo "  make low          Run low load test"
	@echo "  make high         Run high load test"
	@echo "  make spiky        Run spiky load test"
	@echo "  make clean        Stop & remove all worker containers"
	@echo "  make run          Run all necessary functions"

# -------- Build worker image --------
.PHONY: build
build:
	docker build -t $(IMAGE_NAME) .

# -------- Run load balancer --------
.PHONY: lb
lb:
	$(PYTHON) load_balancer.py

# -------- Run autoscaler --------
.PHONY: autoscaler
autoscaler: build
	$(PYTHON) autoscaler.py

# -------- Load tests --------
.PHONY: low
low:
	$(PYTHON) test_load.py low

.PHONY: high
high:
	$(PYTHON) test_load.py high

.PHONY: spiky
spiky:
	$(PYTHON) test_load.py spiky

# -------- Runs all --------
.PHONY: run
run: build
	@echo "Starting Load Balancer..."
	@python3 load_balancer.py & \
	echo "Starting Autoscaler..." && \
	python3 autoscaler.py
	
# -------- Cleanup --------
.PHONY: clean
clean:
	@echo "Stopping and removing worker containers..."
	@docker ps -q --filter ancestor=$(IMAGE_NAME) | xargs -r docker stop
	@docker ps -aq --filter ancestor=$(IMAGE_NAME) | xargs -r docker rm