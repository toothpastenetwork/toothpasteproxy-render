FROM python:3.12-slim

# Required system dependencies for Chromium (Playwright)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk-bridge2.0-0 libxss1 libgtk-3-0 libasound2 \
    libxshmfence1 libgbm1 libdrm2 libxrandr2 libxdamage1 libxcomposite1 \
    libxinerama1 libx11-xcb1 libxext6 libxi6 \
    ca-certificates fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    python -m playwright install --with-deps

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "2", "--loop", "uvloop"]
