# syntax=docker/dockerfile:1
# Self-contained Python reference simulator. NetLogo/DEVSJAVA are NOT bundled.
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="Cyclistics" \
      org.opencontainers.image.description="Reference bicycle-lane discrete-event simulator"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# No pip download is required; current runtime is entirely Python standard library.
RUN groupadd --system --gid 10001 cyclistics \
    && useradd --system --uid 10001 --gid cyclistics --home-dir /app cyclistics \
    && mkdir -p /app/outputs \
    && chown -R cyclistics:cyclistics /app

COPY --chown=cyclistics:cyclistics src/ ./src/
COPY --chown=cyclistics:cyclistics tests/ ./tests/

USER cyclistics

CMD ["python", "-m", "cyclistics", "--output-dir", "/app/outputs"]
