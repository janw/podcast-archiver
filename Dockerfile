FROM python:3.6.2-alpine
VOLUME /data

# Copy the python files in the container
COPY ./podcast_archiver.py /app/
COPY ./requirements.txt /app/
WORKDIR app

# install the requirements
RUN pip install --no-cache-dir -r requirements.txt

# run the archiver
CMD ["python", "./podcast_archiver.py", "--opml=/data/feeds.opml", "--dir=/data/", "--subdirs", "--slugify"]
