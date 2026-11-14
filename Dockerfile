# syntax=docker/dockerfile:1
# Self-contained Python reference simulator plus source-only NetLogo structure tests.
# NetLogo/DEVS-Suite runtimes are NOT bundled.
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="Cyclistics" \
      org.opencontainers.image.description="Reference bicycle-lane discrete-event simulator"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN groupadd --system --gid 10001 cyclistics \
    && useradd --system --uid 10001 --gid cyclistics --home-dir /app cyclistics \
    && mkdir -p /app/outputs \
    && chown -R cyclistics:cyclistics /app

COPY --chown=cyclistics:cyclistics src/ ./src/
COPY --chown=cyclistics:cyclistics tests/ ./tests/
COPY --chown=cyclistics:cyclistics netlogo/ ./netlogo/

USER cyclistics

CMD ["python", "-m", "cyclistics", "--output-dir", "/app/outputs"]
