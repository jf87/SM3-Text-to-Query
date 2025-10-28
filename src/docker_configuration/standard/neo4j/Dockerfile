FROM python:3.9-slim

WORKDIR /app

# Install git and required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install specific neo4j repository dependecies
COPY ./src/docker_configuration/standard/neo4j/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run python script
CMD ["python", "ingest.py"]

# Copy your data folder
#COPY data /data

# Create script to run ingest
#COPY src/neo4j/run_neo4j_ingest.sh /app/run_neo4j_ingest.sh
#RUN chmod +x /app/run_neo4j_ingest.sh
#RUN touch /app/run_neo4j_ingest.sh && \
#    chmod +x /app/run_neo4j_ingest.sh


# Run the ingest script
#CMD ["/app/run_neo4j_ingest.sh"]
#CMD ["/bin/bash", "/app/run_neo4j_ingest.sh"]