FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (leveraging Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure entrypoint is executable
RUN chmod +x /entrypoint.sh

# Define the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
