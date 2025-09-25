FROM docker.io/library/python:3.13-alpine3.22

ENV \
    CRYPTOGRAPHY_DONT_BUILD_RUST=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=true \
    UV_SYSTEM_PYTHON=true \
    UV_EXTRA_INDEX_URL="https://wheel-index.linuxserver.io/alpine-3.22/"

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY arr_tagsync/ ./arr_tagsync/
COPY main.py ./

RUN \
    apk add --no-cache \
        ca-certificates \
        catatonit \
    && \
    pip install uv \
    && uv sync --frozen --no-dev \
    && chown -R root:root /app && chmod -R 755 /app \
    && pip uninstall --yes uv \
    && rm -rf /root/.cache /root/.cargo /tmp/* /app/bin/bin

USER nobody:nogroup

ENTRYPOINT ["/usr/bin/catatonit", "--", "/app/.venv/bin/python", "-m", "arr_tagsync.cli"]
CMD ["--help"]
