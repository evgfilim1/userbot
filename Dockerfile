FROM python:3.10-slim

WORKDIR /app

RUN useradd -rUd /app userbot

COPY --chown=userbot:userbot requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=userbot:userbot *.py ./

RUN mkdir -pm700 /data && chown -R userbot:userbot /data
VOLUME /data

USER userbot:userbot
ENTRYPOINT ["/usr/local/bin/python", "/app/app.py"]