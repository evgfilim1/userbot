FROM python:3.10-slim

WORKDIR /app

RUN useradd -Ud /app userbot

COPY --chown=userbot:userbot requirements.txt ./
# FIXME (2022-05-12): final image is too big because ffmpeg dependencies are too big
RUN pip install --no-cache-dir -r requirements.txt \
    && apt update \
    && apt install -y --no-install-recommends ffmpeg libmagic1 \
    && apt clean

COPY --chown=userbot:userbot userbot ./userbot

RUN mkdir -pm700 /data && chown -R userbot:userbot /data
VOLUME /data

USER userbot:userbot
ENTRYPOINT ["/usr/local/bin/python", "-m", "userbot"]