.PHONY: help setup certs up down test benchmark clean

help:
	@echo "NEXUS: Real-Time Adaptive Digital Twin & Decision Engine"
	@echo "Available targets:"
	@echo "  setup        - Create virtual environment and install dependencies"
	@echo "  certs        - Generate mTLS Root CA and certificates"
	@echo "  up           - Start infrastructure with Docker Compose"
	@echo "  down         - Stop Docker Compose services"
	@echo "  test         - Run full pytest test suite"
	@echo "  benchmark    - Run telemetry load and latency benchmarks"
	@echo "  experiments  - Run research experiments A through E"
	@echo "  clean        - Clean temporary cache and build artifacts"

setup:
	python -m venv .venv
	./.venv/bin/pip install -r requirements.txt

certs:
	python scripts/generate_certs.py

up:
	docker compose up -d

down:
	docker compose down

test:
	pytest tests/ -v

benchmark:
	python benchmarks/run_benchmark.py

experiments:
	python scripts/run_experiments.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov
