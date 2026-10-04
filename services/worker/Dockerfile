# Runs the ingest worker (`python -m worker`) and the eval CLI (`python -m eval`).
FROM python:3.11.17-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH" \
    CONFIG_DIR=/app/config PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/pmo_core/pyproject.toml packages/pmo_core/
COPY services/api/pyproject.toml services/api/
COPY services/worker/pyproject.toml services/worker/
COPY services/eval/pyproject.toml services/eval/
RUN uv sync --frozen --no-dev --package askpmo-worker --package askpmo-eval --no-install-workspace
COPY packages packages
COPY services/worker services/worker
COPY services/eval services/eval
RUN uv sync --frozen --no-dev --package askpmo-worker --package askpmo-eval
COPY config config
CMD ["python", "-m", "worker"]
