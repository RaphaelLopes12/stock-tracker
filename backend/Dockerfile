FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir pip --upgrade && \
    pip install --no-cache-dir .

# Copy application
COPY . .

# Convert line endings and make start script executable
RUN dos2unix start.sh && chmod +x start.sh

# Run migrations and start the application
CMD ["./start.sh"]
