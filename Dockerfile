# Dockerfile for the Code Team's Data Processor (CT-002)

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the core files into the container
# We copy setup.py and requirements first to leverage Docker's build cache
COPY setup.py .
COPY README.md .
COPY .env .
COPY scripts /app/scripts
COPY src /app/src

# Install the package and its dependencies
# The package name is defined in setup.py as 'meta_orchestration_core'
RUN pip install .

# The Code Team's service requires the MQ directories to exist
# These directories are defined in the .env file
# We create them here to ensure the container starts correctly
RUN mkdir -p /app/parallel_orchestration/mq/disk_usage/new
RUN mkdir -p /app/parallel_orchestration/mq/disk_usage/archive

# Set the environment variables from the .env file
# NOTE: In a real production environment, these would be passed securely
# via Kubernetes Secrets or Docker Compose environment variables.
# For this simulation, we load them via the load_env script.

# Command to run the MQ listener (the Code Team's service)
# This uses the entry point defined in setup.py
CMD ["orchestration-listener"]
