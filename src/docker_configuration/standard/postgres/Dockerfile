FROM python:3.9-slim
WORKDIR /app
# Installing system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
# Install repository dependecies
COPY ./src/docker_configuration/standard/postgres/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Mount of the respective files needed for that specific container

#COPY ../../src/postgres/setup-postgres.py .

# Run python script
CMD ["python", "setup-postgres.py"]