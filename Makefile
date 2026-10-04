# askPMO — local workflow. Recipes avoid shell-specific syntax so they run under sh or cmd.
PROFILES ?= full
SPLIT ?= all
COMPOSE = docker compose
# Web tooling runs in a pinned Node container (host Node version does not matter).
export MSYS_NO_PATHCONV=1
WEB_RUN = docker run --rm -v "$(CURDIR)/web:/web" -v askpmo_web_node_modules:/web/node_modules -w /web node:20.20.2-alpine

.PHONY: web-build up down reset logs check-env seed split eval gate test test-int lint format web-types

up:
	$(COMPOSE) up -d --build --wait

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

check-env:
	uv run python tools/check_env.py tools/seed.py

seed:
	uv run python tools/seed.py

split:
	$(COMPOSE) run --rm eval split --seed 42

eval:
	$(COMPOSE) run --rm eval run --profiles $(PROFILES) --split $(SPLIT)

gate:
	$(COMPOSE) run --rm eval gate $(RUN) --phase $(PHASE)

test:
	uv run pytest tests/unit tests/contract

test-int:
	uv run pytest tests/integration -m integration

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy packages/pmo_core/src services/api/src services/worker/src services/eval/src tools/check_env.py tools/seed.py
	$(WEB_RUN) sh -c "npm ci --no-audit --no-fund --loglevel=error && npm run lint && npm run typecheck"

format:
	uv run ruff check --fix .
	uv run ruff format .

web-types:
	uv run python tools/export_openapi.py web/openapi.json
	$(WEB_RUN) sh -c "npm ci --no-audit --no-fund --loglevel=error && npm run gen-types"

web-build:
	$(WEB_RUN) sh -c "npm ci --no-audit --no-fund --loglevel=error && npm run build"
