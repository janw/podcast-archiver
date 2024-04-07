FROM python:3.12-slim as venv

LABEL maintainer="Jan Willhaus <mail@janwillhaus.de>"

ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=1.8.2

WORKDIR /src
COPY pyproject.toml poetry.lock ./

RUN set -e; \
    pip install -U --no-cache-dir pip "poetry~=$POETRY_VERSION"; \
    python -m venv /venv; \
    . /venv/bin/activate; \
    poetry install \
        --no-interaction \
        --no-directory \
        --no-root \
        --only main

FROM python:3.12-slim

ENV PATH=/venv/bin:$PATH
ENV PODCAST_ARCHIVER_ARCHIVE_DIRECTORY=/archive

RUN set -e; \
    apt-get update; \
    apt-get install -y --no-install-recommends 'tini=0.19.*'; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

COPY --from=venv /venv /venv
COPY ./podcast_archiver /podcast_archiver

VOLUME [ "/archive" ]

ENTRYPOINT [ "tini", "--", "python", "-m", "podcast_archiver.cli"]
CMD [ "--help" ]
