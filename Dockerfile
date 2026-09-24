# stage 1 uv builder'
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN uv venv /opt/venv

RUN uv pip install --python /opt/venv --no-cache-dir -r pyproject.toml

# stage 2
FROM python:3.12-slim-bookworm AS runner

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal32 \
    libproj25 \
    libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

COPY . /app

CMD ["python", "main.py"]