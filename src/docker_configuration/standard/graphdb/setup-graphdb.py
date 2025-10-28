import csv
import json
import logging
from rdflib import Graph, URIRef, Literal
from urllib.parse import quote
import argparse
import time
from tqdm import tqdm
import yaml
import requests
import os
from synthea_rdf.graph import GraphBuilder
from pathlib import PurePath, Path
"""

"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = dict()
class LocalServerError(Exception):
    pass

class LocalServer(object):

    def __init__(self):
        self.server_uri = config['server_uri']
        self.repository = config['repository']
        self.repository_url = f"{config['server_uri']}/repository/{config['repository']}"
        self.username = config.get('username', 'admin')
        self.password = config.get('password', 'root')
        self.auth = (self.username, self.password)
        self.configuration = {
            "id": self.repository,
            "title": "SM3 Repository",
            "type": "file-repository",
            "params": {
                "ruleset": {
                    "id": "owl-horst-optimized",
                    "type": "builtin"
                },
                "storage": {
                    "type": "native",
                    "options": {
                        "entityIndexSize": "200000",
                        "entityIdSize": "32"
                    }
                }
            }
        }
        self.max_retries = 3
        self.retry_delay = 2

    def make_repository(self):
        try:
            check_repo = requests.get(f"{self.server_uri}/rest/repositories")
            if check_repo.status_code == 200:
                existing_repos = check_repo.json()
                if any(repo.get('id') == self.repository for repo in existing_repos):
                    delete_response = requests.delete(
                        f"{self.server_uri}/rest/repositories/{self.repository}"
                    )
                    if delete_response.status_code not in (200, 204):
                        print(f"Failed to delete existing repository: {delete_response.status_code}")
                        return delete_response.status_code
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'repo-config.ttl')
            files = {
                'config': ('repo-config.ttl', open(config_path, 'rb'), 'application/x-turtle')
            }
            create_response = requests.post(
                f"{self.server_uri}/rest/repositories",
                files=files
            )
            files['config'][1].close()
            return create_response.status_code
        except FileNotFoundError:
            print(f"Config file not found at: {config_path}")
            return 500
        except Exception as e:
            print(f"Error: {str(e)}")
            return 500

    def create_repository(self):
        if not self.configuration:
            raise LocalServerError("Configuration not loaded")

        for attempt in range(self.max_retries):
            try:
                response = self.make_repository()
                if response == 200 or response == 201 or response == 400:
                    logger.info("Repository created successfully")
                    return True
                else:
                    logger.error(f"Failed attempt {attempt + 1} with status code: {response}")
                    time.sleep(self.retry_delay)

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
                print(e)
                time.sleep(self.retry_delay)
        raise LocalServerError(f"Failed to create repository after {self.max_retries} attempts")

    def import_ttl_files(self, ttl_directory):
        graphdb_url = f'{self.server_uri}/repositories/{self.repository}/statements'
        headers = {
            'Content-Type': 'application/x-turtle'
        }
        print(ttl_directory)
        print(os.walk(ttl_directory))
        for root, dirs, files in os.walk(ttl_directory):
            for file in files:
                if file.endswith('.ttl'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'rb') as f:
                        response = requests.post(
                            graphdb_url,
                            headers=headers,
                            data=f
                        )
                        if response.status_code == 204:
                            print(f"{file} imported successfully")
                        else:
                            print(f"{file} imported failed")

    def run_test_query(self):
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX syn: <https://knacc.umbc.edu/dae-young/kim/ontologies/synthea#> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX pl: <http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral> 
        SELECT DISTINCT ?first ?last
        WHERE {
        ?organization a syn:Organization;
        syn:id ?organizationId; syn:name 'ROYAL OF FAIRHAVEN NURSING CENTER'^^pl:.
        ?encounter a syn:Encounter;
        syn:organizationId ?organizationId;
        syn:patientId ?patientId. ?patient a syn:Patient;
        syn:id ?patientId; syn:first ?first; syn:last ?last. 
        }
        """
        headers = {
            'Accept': 'application/sparql-results+json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(
            f"{self.server_uri}/repositories/{self.repository}",
            headers=headers,
            data={'query': query}
        )
        #print(response.headers)
        #print(response.status_code)
        if response.status_code != 200:
            print(f"Response Content: {response.text}")
            return False, f"Query failed with status code: {response.status_code}. Response: {response.text}"

        try:
            results = response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"Failed to decode JSON. Raw response: {response.text}")
            return False, "Invalid JSON response from server"

        if 'results' not in results or 'bindings' not in results['results']:
            return False, "Invalid response format from server"
        formatted_results = []
        for binding in results['results']['bindings']:
            formatted_results.append({
                'first': binding['first']['value'],
                'last': binding['last']['value']
            })
        print("\nQuery Results:")
        for result in formatted_results:
            print(f"First Name: {result['first']}, Last Name: {result['last']}")
        expected_result = {'first': 'Glendora96', 'last': 'Tillman293'}
        if any(r['first'] == expected_result['first'] and
               r['last'] == expected_result['last']
               for r in formatted_results):
            print("\n✅ Test passed: Found expected person Glendora96 Tillman293")
            test_passed = True
        else:
            print("\n❌ Test failed: Could not find expected person Glendora96 Tillman293")
            test_passed = False
# global defined functions and helper functions
def load_config(configuration):
    global config
    with open(configuration) as config_file:
        config = yaml.load(config_file, yaml.SafeLoader)


def main():

    # Loading the configuration of the graphdb database
    configuration_file = 'config_graphdb.yml'
    load_config(configuration_file)
    server = LocalServer()
    # Creation of local repository
    server.create_repository()
    # Loading of the ttl files
    ttl_directory = "/app/synthea-rdf-converter-fork/temporary_ttl_files"
    server.import_ttl_files(ttl_directory)
    # Run Experiment query
    print(server.run_test_query())

if __name__ == "__main__":
    main()

