# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    sudo \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install cloudflared
RUN curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && \
    dpkg -i cloudflared.deb && \
    rm cloudflared.deb

# Configure git to trust the /app directory (fixes "dubious ownership" error when mounting volumes)
RUN git config --global --add safe.directory /app

# Set the working directory
WORKDIR /app

# Run the startup script with the refresh flag
CMD ["/bin/bash", "./startup.sh", "--refresh"]