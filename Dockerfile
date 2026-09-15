# syntax=docker/dockerfile:1

# Shared base: Python + uv, nothing environment-specific yet.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

# --- dev: used by docker-compose.yml, source is bind-mounted over this ---
FROM base AS dev
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . .
EXPOSE 8000
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- prod stage added in Day 6 (docker-compose.prod.yml target: prod) ---
