FROM docker.io/library/python:3.13-alpine3.22

WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY arrem_sync/ /app/arrem_sync/
COPY --from=ghcr.io/astral-sh/uv:0.9.24@sha256:816fdce3387ed2142e37d2e56e1b1b97ccc1ea87731ba199dc8a25c04e4997c5 /uv /uvx /bin/

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
