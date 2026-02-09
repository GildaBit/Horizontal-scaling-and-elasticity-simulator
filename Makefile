# AUTHOR: Gilad Bitton
# RedID: 130621085

# -------- Configuration --------
IMAGE_NAME = worker-app:latest
PYTHON = python3
VENV_DIR := venv
PIP := $(VENV_DIR)/bin/pip

# -------- Targets --------

.PHONY: help venv install venv-clean venv-deactivate build lb autoscaler low high spiky run clean
help:
	@echo "Available targets:"
	@echo "  make venv         Create the virtual environment (./venv)"
	@echo "  make install      Install Python deps into the venv (after activation)"
	@echo "  make venv-deactivate  Hint to deactivate the venv"
	@echo "  make venv-clean   Delete the virtual environment"
	@echo "  make build        Build worker Docker image"
	@echo "  make lb           Run load balancer"
	@echo "  make autoscaler   Run autoscaler (builds image first)"
	@echo "  make low          Run low load test"
	@echo "  make high         Run high load test"
	@echo "  make spiky        Run spiky load test"
	@echo "  make clean        Stop & remove all worker containers"
	@echo "  make run          Run all necessary functions"

# -------- Virtual environment helpers --------
venv:
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment created in ./$(VENV_DIR)"

install:
	$(PIP) install -r requirements.txt

venv-clean:
	rm -rf $(VENV_DIR)
	@echo "Virtual environment removed."

venv-deactivate:
	@echo "To deactivate: run 'deactivate' in your shell (make cannot deactivate for you)."

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
	@$(PYTHON) load_balancer.py & \
	echo "Starting Autoscaler..." && \
	$(PYTHON) autoscaler.py

# -------- Cleanup --------
.PHONY: clean
clean:
	@echo "Stopping and removing worker containers..."
	@docker ps -q --filter ancestor=$(IMAGE_NAME) | xargs -r docker stop
	@docker ps -aq --filter ancestor=$(IMAGE_NAME) | xargs -r docker rm
