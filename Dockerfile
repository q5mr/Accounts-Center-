FROM python:3.10-slim

# تثبيت أدوات الشبكة الأساسية داخل السيرفر
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# تثبيت المكتبات مع تحديث httpx
RUN pip install --no-cache-dir python-telegram-bot==20.8 httpx[http2]

CMD ["python", "main.py"]
