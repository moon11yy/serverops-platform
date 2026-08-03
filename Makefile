SHELL := /bin/bash

.PHONY: env up down restart logs ps test lint scan register fail-disk heal-disk demo clean

env:
	@test -f .env || cp .env.example .env
	@echo ".env is ready. Replace the example passwords before first use."

up:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

test:
	python3 -m pytest

lint:
	ruff check .

register:
	./scripts/register-demo-server.sh

scan:
	curl --fail --silent --show-error -X POST http://localhost:$${COLLECTOR_PORT:-8001}/scan | python3 -m json.tool

fail-disk:
	curl --fail --silent --show-error -X POST http://localhost:$${SIMULATOR_PORT:-9000}/control/disk-failure | python3 -m json.tool

heal-disk:
	curl --fail --silent --show-error -X POST http://localhost:$${SIMULATOR_PORT:-9000}/control/disk-healthy | python3 -m json.tool

demo:
	./scripts/demo.sh

clean:
	docker compose down -v --remove-orphans
