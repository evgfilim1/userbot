FROM python:3.10-slim

WORKDIR /app

RUN useradd -rU selfbot

COPY --chown=selfbot:selfbot requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=selfbot:selfbot *.py ./

RUN mkdir -pm700 /data && chown -R selfbot:selfbot /data
VOLUME /data

USER selfbot:selfbot
ENTRYPOINT ["/usr/local/bin/python", "/app/app.py"]