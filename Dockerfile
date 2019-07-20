FROM python:3.7-alpine
LABEL maintainer="Jan Willhaus <mail@janwillhaus.de>"

COPY pyproject.toml poetry.lock ./

RUN \
    wget -q -O - https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && \
    $HOME/.poetry/bin/poetry config settings.virtualenvs.create false && \
    $HOME/.poetry/bin/poetry --no-interaction install --no-dev && \
    rm -rf $HOME/.poetry pyproject.toml poetry.lock

WORKDIR /app
COPY podcast_archiver ./podcast_archiver

ENTRYPOINT [ "python", "-m", "podcast_archiver" ]
