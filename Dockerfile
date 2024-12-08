# The builder image, used to build the virtual environment
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev


COPY ./pyproject.toml ./uv.lock /app/

COPY ./dsmr_client /app/dsmr_client

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable


# The runtime image, used to just run the code provided its virtual environment
FROM python:3.12-slim-bookworm AS runtime

ENV PATH=/app/.venv/bin:$PATH

WORKDIR /app

COPY --from=builder --chown=app:app /app /app

CMD ["python", "-m", "dsmr_client.main"]
