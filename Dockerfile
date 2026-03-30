FROM python:3.10-slim

# Install system dependencies including sqlite3
RUN apt-get update && apt-get install -y \
    libsqlite3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "tempest.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "600"]
