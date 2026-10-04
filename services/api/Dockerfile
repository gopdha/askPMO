FROM python:3.11.17-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH" \
    CONFIG_DIR=/app/config PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/pmo_core/pyproject.toml packages/pmo_core/
COPY services/api/pyproject.toml services/api/
COPY services/worker/pyproject.toml services/worker/
COPY services/eval/pyproject.toml services/eval/
RUN uv sync --frozen --no-dev --package askpmo-api --no-install-workspace
COPY packages packages
COPY services/api services/api
RUN uv sync --frozen --no-dev --package askpmo-api
COPY config config
EXPOSE 8000
CMD ["python", "-m", "api"]
