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

# update the respective requirements:
COPY ./src/docker_configuration/standard/graphdb/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run both files: 1. Creation of TTL 2. Upload of TTL files to repo.
CMD ["sh", "-c", "python ./synthea-rdf-converter-fork/conversion.py&& python setup-graphdb.py" ]
