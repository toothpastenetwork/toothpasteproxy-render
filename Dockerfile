FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install Chromium dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg unzip curl fonts-liberation libnss3 libatk-bridge2.0-0 libxss1 \
    libgtk-3-0 libasound2 libxshmfence1 libgbm1 libdrm2 libxrandr2 libxdamage1 \
    libxcomposite1 libxinerama1 libxcursor1 libx11-xcb1 libxext6 libxi6 \
    ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    python -m playwright install --with-deps

EXPOSE 8080

CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8080"]
