# Dockerfile
FROM python:3.12-slim

# Workdir inside container
WORKDIR /app

# Install Python deps first (better build cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src

# Create data directory (DB + JSON files will live here)
RUN mkdir -p data/events data/games

# No buffering so logs appear immediately
ENV PYTHONUNBUFFERED=1

# Run your main script
CMD ["python", "-m", "src.main"]