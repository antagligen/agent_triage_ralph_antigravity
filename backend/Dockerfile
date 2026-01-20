FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
# Install system dependencies if needed (none for now)

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src ./src
COPY config.yaml .
# Copy static files if they are still served by backend for now (though plan says separate microservices, backend code references it)
COPY static ./static
COPY .env.example .
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
# Expose port
EXPOSE 8000

# Run the application
# We use standard uvicorn command assuming we mount/env vars correctly
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
