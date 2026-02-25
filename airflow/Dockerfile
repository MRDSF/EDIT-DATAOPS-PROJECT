# Use the official Airflow image
FROM apache/airflow:2.9.3-python3.11

# Switch to root to install system packages
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to the airflow user
USER airflow

# Copy requirements.txt into the container
COPY requirements.txt /requirements.txt

# Install Python packages from requirements.txt (no constraints)
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /requirements.txt

# Set working directory
WORKDIR /workspace