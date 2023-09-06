# The builder image, used to build the virtual environment
FROM python:3.11-buster as builder

ENV POETRY_VERSION=1.4.2 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/opt/.cache 

ENV PATH=$POETRY_HOME/bin:$PATH

RUN curl -sSL https://install.python-poetry.org | python3 - 

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.11-slim-buster as runtime

ENV VENV_PATH=/app/.venv
ENV PATH=$VENV_PATH/bin:$PATH

WORKDIR /app

COPY --from=builder ${VENV_PATH} ${VENV_PATH}

COPY ./dsmr_client /app/dsmr_client

ENTRYPOINT ["python", "-m", "dsmr_client.main"]
