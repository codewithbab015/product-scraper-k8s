FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

COPY requirements.txt .

RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

RUN /opt/venv/bin/playwright install firefox

COPY . .

FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libgtk-3-0 libasound2 libxss1 libx11-xcb1 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app
COPY --from=builder /opt/venv /opt/venv

COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

ENV PATH="/opt/venv/bin:${PATH}"   
ENV PYTHONUNBUFFERED=1             
ENV PLAYWRIGHT_BROWSERS_PATH="/root/.cache/ms-playwright"

ENTRYPOINT ["python", "run_scraper.py"]