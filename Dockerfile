# The base image we want to inherit from
FROM python:3.11.5-buster AS app

# set work directory
WORKDIR /app

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    # pip:
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry:
    POETRY_VERSION=1.5.0 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME="/opt/poetry"

# System deps:
RUN apt update && apt install --no-install-recommends -y \
    bash build-essential curl gettext git libpq-dev wget cron \
    # Cleaning cache:
    && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man \
    && apt-get clean \
    # Install poetry:
    && pip install "poetry==$POETRY_VERSION" && poetry --version

COPY pyproject.toml poetry.lock /app/
RUN --mount=type=cache,target=/home/.cache/pypoetry/cache \
    --mount=type=cache,target=/home/.cache/pypoetry/artifacts \
    poetry install --no-root

COPY bin/ ./bin
RUN chmod +x bin/*

ARG DEBUG
ENV DEBUG="${DEBUG}" \
    PYTHONUNBUFFERED="True" \
    PYTHONPATH="."

COPY . .

WORKDIR /app/src

EXPOSE 8000

CMD ["poetry", "run", "python3", "src/main.py"]
