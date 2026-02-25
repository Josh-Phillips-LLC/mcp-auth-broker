FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir . && \
    useradd --create-home --uid 10001 appuser && \
    chown -R appuser:appuser /app

USER appuser

CMD ["python", "-m", "mcp_auth_broker.cli"]
