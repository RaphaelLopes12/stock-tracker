FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir pip --upgrade && \
    pip install --no-cache-dir .

# Copy application
COPY . .

# Run migrations and start the application
CMD python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
