FROM python:3.9-slim

LABEL maintainer="Jan Willhaus <mail@janwillhaus.de>"

ENV PYTHONUNBUFFERED=1

COPY requirements.txt /

RUN set -e; \
    apt-get update; \
    apt-get install -y --no-install-recommends 'tini=0.19.*'; \
    pip install --no-cache-dir -r /requirements.txt; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

COPY ./podcast_archiver /podcast_archiver

ENTRYPOINT [ "tini", "--", "python", "-m", "podcast_archiver"]
CMD [ "--help" ]
