FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY . .

RUN uv sync --frozen

CMD ["uv", "run", "uvicorn", "open_telemetry_experiment_worker.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
