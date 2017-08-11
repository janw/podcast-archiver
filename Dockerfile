FROM python:3.6.2-alpine

# VOLUME /data

# Copy the python files in the container
COPY ./podcast_archiver.py /app/
COPY ./requirements.txt /app/
WORKDIR app

RUN pip install --no-cache-dir -r requirements.txt

# VOLUME ["/data"]
# COPY ./data /data/

CMD ["ls", "-lah", "/data"]
# CMD ["python", "./podcast_archiver.py", "--opml=/data/feeds.opml", "--dir=/data/", "--subdirs", "--slugify", "-vvvvv"]
