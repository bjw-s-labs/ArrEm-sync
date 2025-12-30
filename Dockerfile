FROM docker.io/library/python:3.13-alpine3.22

WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY arrem_sync/ /app/arrem_sync/
COPY --from=ghcr.io/astral-sh/uv:0.9.21@sha256:15f68a476b768083505fe1dbfcc998344d0135f0ca1b8465c4760b323904f05a /uv /uvx /bin/

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
