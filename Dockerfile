# app/Dockerfile

FROM python:3.11-slim

WORKDIR /

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Install uv and dependencies from pyproject.toml
RUN python -m venv .venv \
    && . .venv/bin/activate \
    && pip install --no-cache-dir --upgrade pip \
    && pip install uv \
    && uv sync

# Set the virtual environment as default for the container
ENV PATH="/.venv/bin:$PATH"

EXPOSE 8501

ENTRYPOINT ["chainlit", "run", "app.py", "--port=8501", "--host=0.0.0.0"]