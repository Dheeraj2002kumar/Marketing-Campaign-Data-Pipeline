# Production-ready Dockerfile for Marketing Campaign Data Pipeline
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and configurations
COPY src/ /app/src/
COPY sql/ /app/sql/
COPY data/ /app/data/
COPY reports/ /app/reports/
COPY logs/ /app/logs/
COPY docs/ /app/docs/
COPY main.py /app/main.py

# Default execution entrypoint runs the ETL pipeline
CMD ["python", "main.py"]
