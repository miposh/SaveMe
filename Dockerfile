FROM python:3.12-slim

ARG TZ=Europe/Moscow
ENV TZ="$TZ"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    mediainfo \
    rsync \
    fonts-noto-core \
    fonts-noto-extra \
    fonts-kacst-one \
    fonts-noto-cjk \
    fonts-indic \
    fonts-noto-color-emoji \
    fontconfig \
    libass9 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Amiri Arabic font
RUN git clone --depth 1 https://github.com/aliftype/amiri.git /tmp/amiri \
    && mkdir -p /usr/share/fonts/truetype/amiri \
    && cp /tmp/amiri/fonts/*.ttf /usr/share/fonts/truetype/amiri/ \
    && fc-cache -fv \
    && rm -rf /tmp/amiri

WORKDIR /app

COPY requirements_new.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-install yt-dlp with pre-releases
RUN pip install --no-cache-dir --pre "yt-dlp[default,curl-cffi]"

COPY . .

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 5555

CMD ["/usr/local/bin/docker-entrypoint.sh"]
