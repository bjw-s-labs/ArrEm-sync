FROM docker.io/library/python:3.13-alpine3.22

WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY arrem_sync/ /app/arrem_sync/
COPY --from=ghcr.io/astral-sh/uv:0.10.4@sha256:4cac394b6b72846f8a85a7a0e577c6d61d4e17fe2ccee65d9451a8b3c9efb4ac /uv /uvx /bin/

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
