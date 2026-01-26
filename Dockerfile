FROM docker.io/library/python:3.13-alpine3.22

WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY arrem_sync/ /app/arrem_sync/
COPY --from=ghcr.io/astral-sh/uv:0.9.27@sha256:143b40f4ab56a780f43377604702107b5a35f83a4453daf1e4be691358718a6a /uv /uvx /bin/

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
