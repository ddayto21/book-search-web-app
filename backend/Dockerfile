# syntax=docker/dockerfile:1

# 1) Use the official Python slim image
FROM python:3.10-slim AS base

# 2) Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.0.1

# 3) Install system dependencies and Poetry, then clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && curl -sSL https://install.python-poetry.org | python3 - \
  && ln -s /root/.local/bin/poetry /usr/local/bin/poetry \
  && apt-get remove -y curl \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*

# 4) Set the working directory
WORKDIR /app

# 5) Copy only dependency files first (leverage Docker layer caching)
COPY pyproject.toml poetry.lock README.md ./

# 6) Install dependencies without dev packages

RUN poetry install --no-interaction --no-ansi

# 7) Copy application code
COPY . .

# 8) Remove any extraneous local/dev files
RUN rm -rf .env .env.tests node_modules \
    .pytest_cache .mypy_cache .ruff_cache __pycache__ \
    tests

# 9) Expose the application port
EXPOSE 8000

# 10) Run FastAPI via Uvicorn
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]