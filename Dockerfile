FROM jrottenberg/ffmpeg:5.1-ubuntu2004

WORKDIR /app

RUN useradd -Ud /app userbot \
    && mkdir -pm700 /data \
    && chown -R userbot:userbot /data \
    && apt update \
    && apt install -y --no-install-recommends gpg dirmngr gpg-agent \
    && echo 'deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu focal main' >>/etc/apt/sources.list \
    && echo 'deb-src https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu focal main' >>/etc/apt/sources.list \
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv F23C5A6CF475977595C89F51BA6932366A755776 \
    && apt update \
    && apt install -y --no-install-recommends python3.10 python3.10-distutils libmagic1 curl \
    && { curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10; } \
    && apt autoremove -y gpg dirmngr gpg-agent curl --purge \
    && apt clean -y \
    && rm -rf /var/lib/apt/* /root/.cache /var/log/* /var/cache/*

VOLUME /data

COPY requirements.txt ./
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

COPY locales ./locales
COPY userbot ./userbot

USER userbot:userbot
ENTRYPOINT ["/usr/bin/env", "python3.10", "-m", "userbot"]
