.PHONY: install dev-install test lint format clean run docker-build docker-run setup

# Default Python interpreter
PYTHON := python3
PIP := pip3

install:
	$(PIP) install -e .

dev-install:
	$(PIP) install -e ".[dev]"

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	black --check src/ tests/
	isort --check-only src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

run:
	uvicorn src.web.api_server:app --host 0.0.0.0 --port 8000 --reload

run-prod:
	uvicorn src.web.api_server:app --host 0.0.0.0 --port 8000 --workers 4

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -t ai-manhua-editor:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

setup:
	cp .env.example .env
	mkdir -p output temp cache projects

help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install with dev dependencies"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run linters"
	@echo "  format       - Format code"
	@echo "  run          - Run development server"
	@echo "  run-prod     - Run production server"
	@echo "  clean        - Clean build artifacts"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  setup        - Initial project setup"
