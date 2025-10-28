# Definition of the needed image:
FROM python:3.9-slim
# Definition of workdirketory from which the instance starts
WORKDIR /app
# Installing simple system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install specific mongodb repository dependecies
COPY ./src/docker_configuration/standard/mongodb/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Run specific setup file
CMD ["python", "setup-mongodb.py"]


