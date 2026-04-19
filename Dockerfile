FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.14-slim AS runner

WORKDIR /app

COPY --from=builder /app/.venv ./.venv

COPY src/ ./src/

COPY migrations/ ./migrations/

COPY alembic.ini ./

COPY main.py ./

RUN useradd -r -s /bin/false appuser && chown -R appuser /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"

ENV PYTHONUNBUFFERED=1

ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "main.py"]