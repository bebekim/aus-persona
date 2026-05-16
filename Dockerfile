FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:${PATH}" \
    DAGSTER_HOME="/app/dagster_home"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN cp dbt/aus_personas/profiles.yml.example dbt/aus_personas/profiles.yml
RUN uv sync --frozen

EXPOSE 3000

CMD ["dagster", "dev", "--host", "0.0.0.0", "--port", "3000", "-w", "workspace.yaml"]
