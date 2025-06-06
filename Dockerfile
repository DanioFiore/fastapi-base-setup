FROM python:3.11-slim

# set working directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*


# copy dependency files
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE ${APP_PORT:-8000}

# Default command
CMD ["uvicorn", "app.main:app", "--host", "${APP_HOST:-0.0.0.0}", "--port", "${APP_PORT:-8000}", "--reload"]
