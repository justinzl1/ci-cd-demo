.PHONY: install lint format test docker-build docker-run

IMAGE ?= telemetry-api:local

install:
	pip install -r requirements-dev.txt

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

test:
	pytest -v

docker-build:
	docker build --build-arg APP_VERSION=local -t $(IMAGE) .

docker-run:
	docker run --rm -p 8000:8000 $(IMAGE)
