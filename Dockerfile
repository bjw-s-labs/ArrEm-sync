FROM docker.io/library/python:3.13-alpine3.22

WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY arrem_sync/ /app/arrem_sync/
COPY --from=ghcr.io/astral-sh/uv:0.9.4@sha256:c4089b0085cf4d38e38d5cdaa5e57752c1878a6f41f2e3a3a234dc5f23942cb4 /uv /uvx /bin/

RUN \
    apk add --no-cache \
        ca-certificates \
        catatonit \
    && uv sync --locked --no-dev \
    && chown -R root:root /app && chmod -R 755 /app \
    && rm -rf /root/.cache /root/.cargo /tmp/*

USER nobody:nogroup
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["/usr/bin/catatonit", "--", "arrem-sync"]
