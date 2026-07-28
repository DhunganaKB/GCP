# syntax=docker/dockerfile:1

# Python 3.12 slim keeps the image small and has prebuilt wheels for the deps.
FROM python:3.12-slim

# Fail fast, unbuffered logs (so Cloud Run captures stdout/stderr in real time),
# no .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application package.
COPY app ./app

# Run as a non-root user (Cloud Run doesn't require it, but it's good practice).
RUN useradd --create-home --uid 1000 appuser
USER appuser

# Cloud Run sends traffic to the port named in $PORT (default 8080). Bind to it
# on all interfaces. `exec` makes uvicorn PID 1 so it receives SIGTERM cleanly.
# Shell form is used deliberately so ${PORT} is expanded at runtime.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
