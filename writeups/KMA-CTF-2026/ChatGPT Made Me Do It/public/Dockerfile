FROM node:22-bookworm-slim

ENV USER=user
ENV PORT=3000
ENV FLAG=KMACTF{FAKE_FLAG}
ENV CHROME_BIN=/usr/bin/chromium
ENV PUPPETEER_SKIP_DOWNLOAD=true

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
  && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos '' $USER

WORKDIR /app
COPY deploy/package*.json /app/
RUN npm install --omit=dev
COPY deploy/ /app/
RUN chown -R $USER:$USER /app

USER $USER
EXPOSE $PORT

CMD ["npm", "start"]
