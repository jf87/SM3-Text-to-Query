import pandas as pd
from neo4j import GraphDatabase
import yaml
import datetime
#import gzip
from zipfile import ZipFile
from urllib.parse import urlparse
import boto3
from smart_open import open
import io
import gzip
import pathlib
import ijson
# additional
import logging
import subprocess
import time
"""
This code is adapted from the pyingest library
Source: https://github.com/neo4j-field/pyingest
Original License: Apache-2.0 license

Modifications made for the Synthea healthcare data ingestion into Neo4j.
- Creation of SM3 Neo4j database
- Adjustment of database standard settings 
    - server.memory.heap.initial_size=1G
    - server.memory.heap.max_size=4G
    - server.memory.pagecache.size=2G
    - dbms.memory.transaction.total.max=5G
- Installation of APOC plugin for the database
- Definition of specific data path 
- updated deprecated parameter definition 
"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = dict()
supported_compression_formats = ['gzip','zip', 'none']


class LocalServer(object):


    def __init__(self):
        self._driver = GraphDatabase.driver(config['server_uri'],
                                            auth=(config['admin_user'],
                                                  config['admin_pass']))
        self.db_config={}
        self.database = config['database'] if 'database' in config else 'neo4j'
        if self.database is not None:
            self.db_config['database'] = self.database
        self.basepath = config['basepath'] if 'basepath' in config else '/app/data'

    # Helper function checking the existence of a SM3 database
    def check_sm3_database_existence(self):
        try:
            with self._driver.session(database="system") as session:
                result = session.run("SHOW DATABASES")
                existing_databases = [record["name"] for record in result]
                #lowercase_database_name = str(self.database).lower()
                #lowercase_database_name = 'sm3'
                lowercase_database_name = 'neo4j'
                return lowercase_database_name in existing_databases
        except Exception as e:
            print(f"Error checking the SM3 Neo4j database existence: {str(e)}")
            return False
    # Helper function checking the existence of the respective data
    def check_sm3_data_existence(self):
        try:
            with self._driver.session(**self.db_config) as session:
                # Generic query giving the number of rows in the data:
                result = session.run("MATCH (n) RETURN count(n) as count")
                count = result.single()["count"]
                return count > 0
        except Exception as e:
            print(f"Error checking the existence of data: {str(e)}")
            return False
    # Function, which creates SM3 database if it does not already exist
    def create_sm3_neo4j_database(self):
        if self.check_sm3_database_existence():
            print(f"Database {self.database} already exists")
            return True

        try:
            with self._driver.session(database="system") as session:
                session.run(f"CREATE DATABASE {self.database}")
                print(f"Created SM3 database: {self.database}")
                return True
        except Exception as e:
            print(f"Error creating database: {str(e)}")
            return False

    # Test the database
    def run_db_test(self):
        neo4j_test_query = ["""
                    MATCH (o:Organization {name: 'ROYAL OF FAIRHAVEN NURSING CENTER'})- [:IS_PERFOMED_AT]->(e:Encounter)<-[:HAS_ENCOUNTER]-(p:Patient) 
                    RETURN DISTINCT p.firstName, p.lastName
                """]
        try:
            #with self._driver.session(database="sm3") as session:
            with self._driver.session(database="sm3") as session:
                for i, query in enumerate(neo4j_test_query, 1):
                    print("Query:", query)
                    print("Query result:")
                    results = session.run(query)
                    records = list(results)
                    for record in records:
                        record_tuple = (record['p.firstName'],record['p.lastName'])
                        expected_tuple = ('Glendora96', 'Tillman293')
                        # showing the tuple solution
                        print(f"Record from database as tuple: {record_tuple}")
                        print(f"Expected from database as tuple: {expected_tuple}")

                        if record_tuple == expected_tuple:
                            print("Test passed")
                        else:
                            print("Test failed")
        except Exception as e:
            print(f"Error running test queries :{e}")

    def close(self):
        self._driver.close()

    def load_file(self, file):
        # Set up parameters/defaults
        # Check skip_file first so we can exit early
        skip = file.get('skip_file') or False
        if skip:
            print("Skipping this file: {}", file['url'])
            return

        print("{} : Reading file", datetime.datetime.utcnow())

        # If file type is specified, use that.  Else check the extension.  Else, treat as csv
        type = file.get('type') or 'NA'
        if type != 'NA':
            if type == 'csv':
                self.load_csv(file)
            elif type == 'json':
                self.load_json(file)
            else:
                print("Error! Can't process file because unknown type", type, "was specified")
        else:
            file_suffixes = pathlib.Path(file['url']).suffixes
            if '.csv' in file_suffixes:
                self.load_csv(file)
            elif '.json' in file_suffixes:
                self.load_json(file)
            else:
                self.load_csv(file)

    # Tells ijson to return decimal number as float.  Otherwise, it wraps them in a Decimal object,
    # which angers the Neo4j driver
    @staticmethod
    def ijson_decimal_as_float(events):
        for prefix, event, value in events:
            if event == 'number':
                value = str(value)
            yield prefix, event, value

    def load_json(self, file):
        with self._driver.session(**self.db_config) as session:
            params = self.get_params(file)
            openfile = file_handle(params['url'], params['compression'])
            # 'item' is a magic word in ijson.  It just means the next-level element of an array
            items = ijson.common.items(self.ijson_decimal_as_float(ijson.parse(openfile)), 'item')
            # Next, pool these into array of 'chunksize'
            halt = False
            rec_num = 0
            chunk_num = 0
            rows = []
            while not halt:
                row = next(items, None)
                if row is None:
                    halt = True
                else:
                    rec_num = rec_num+1;
                    if rec_num > params['skip_records']:
                        rows.append(row)
                        if len(rows) == params['chunk_size']:
                            print(file['url'], chunk_num, datetime.datetime.utcnow(), flush=True)
                            chunk_num = chunk_num + 1
                            rows_dict = {'rows': rows}
                            session.run(params['cql'], dict=rows_dict).consume()
                            rows = []

            if len(rows) > 0:
                print(file['url'], chunk_num, datetime.datetime.utcnow(), flush=True)
                rows_dict = {'rows': rows}
                session.run(params['cql'], dict=rows_dict).consume()

        print("{} : Completed file", datetime.datetime.utcnow())

    def get_params(self, file):
        params = dict()
        params['skip_records'] = file.get('skip_records') or 0
        params['compression'] = file.get('compression') or 'none'
        if params['compression'] not in supported_compression_formats:
            print("Unsupported compression format: {}", params['compression'])

        file_url = file['url']
        if self.basepath and file_url.startswith('$BASE'):
            file_url = file_url.replace('$BASE', self.basepath, 1)
        params['url'] = file_url
        print("File {}", params['url'])
        params['cql'] = file['cql']
        params['chunk_size'] = file.get('chunk_size') or 1000
        params['field_sep'] = file.get('field_separator') or ','
        return params

    def load_csv(self, file):
        with self._driver.session(**self.db_config) as session:
            params = self.get_params(file)
            openfile = file_handle(params['url'], params['compression'])

            # - The file interfaces should be consistent in Python but they aren't
            if params['compression'] == 'zip':
                header = openfile.readline().decode('UTF-8')
            else:
                header = str(openfile.readline())

            # Grab the header from the file and pass that to pandas.  This allow the header
            # to be applied even if we are skipping lines of the file
            header = header.strip().split(params['field_sep'])

            # Pandas' read_csv method is highly optimized and fast :-)
            row_chunks = pd.read_csv(openfile, dtype=str, sep=params['field_sep'], on_bad_lines='skip',
                                     index_col=False, skiprows=params['skip_records'], names=header,
                                     low_memory=False, engine='c', compression='infer', header=None,
                                     chunksize=params['chunk_size'])

            for i, rows in enumerate(row_chunks):
                print(params['url'], i, datetime.datetime.utcnow(), flush=True)
                # Chunk up the rows to enable additional fastness :-)
                rows_dict = {'rows': rows.fillna(value="").to_dict('records')}
                session.run(params['cql'],
                            dict=rows_dict).consume()

        print("{} : Completed file", datetime.datetime.utcnow())

    def pre_ingest(self):
        if 'pre_ingest' in config:
            statements = config['pre_ingest']

            with self._driver.session(**self.db_config) as session:
                for statement in statements:
                    session.run(statement)

    def post_ingest(self):
        if 'post_ingest' in config:
            statements = config['post_ingest']

            with self._driver.session(**self.db_config) as session:
                for statement in statements:
                    session.run(statement)


def file_handle(url, compression):
    parsed = urlparse(url)
    if parsed.scheme == 's3':
        path = get_s3_client().get_object(Bucket=parsed.netloc, Key=parsed.path[1:])['Body']
    elif parsed.scheme == 'file':
        path = parsed.path
    else:
        path = url
    #if compression == 'gzip':
    #    return gzip.open(path, 'rt')
    if compression == 'zip':
        # Only support single file in ZIP archive for now
        if isinstance(path, str):
            buffer = path
        else:
            buffer = io.BytesIO(path.read())
        zf = ZipFile(buffer)
        filename= zf.infolist()[0].filename
        return zf.open(filename)
    else:
        return open(path)


def get_s3_client():
    return boto3.Session().client('s3')


def load_config(configuration):
    global config
    with open(configuration) as config_file:
        config = yaml.load(config_file, yaml.SafeLoader)

def wait_for_db(max_retries=60, delay_seconds=2):
    for attempt in range(max_retries):
        try:
            driver = GraphDatabase.driver(config['server_uri'],
                                           auth=(config['admin_user'],
                                                 config['admin_pass']))
            with driver.session(database="system") as session:
                result = session.run("SHOW DATABASES")
                existing_databases = [record["name"] for record in result]
                # lowercase_database_name = str(self.database).lower()
                lowercase_database_name = 'sm3'
                #return lowercase_database_name in existing_databases
            print("Successfully connected to the neo4j sm3 database")
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} to connect to the neo4j sm3 database failed")
            print(f"Error: {e}")
            time.sleep(delay_seconds)
        finally:
            if driver:
                driver.close()

    raise Exception("Could not connect to the neo4j sm3 database after 60 maximum retries")

def main():
    # Definition of location of the configuration file
    configuration = '/app/config_neo4j.yml'

    # Load the respective configuration file
    load_config(configuration)
    if not wait_for_db():
        logger.error("Failed to connect to database")
        return
    #server = LocalServer()
    #configuration = sys.argv[1]

    # No additional checks needed regarding the creation of a new database sm3
    #
    # Reason: Only community image could be pulled
    #
    # dockerimage only directly useable for the community edition
    # if server.check_sm3_database_existence():
    #    if server.check_sm3_data_existence():
    #        print("SM3 data and database already exists in database. Import skipped.")
    #        server.run_db_test()
    #        server.close()
    #        return
        # In the case data has not been loaded, the code below for the loading and saving of data is executed
    #else:
        # print(server.check_sm3_database_existence())
    #    if not server.create_sm3_neo4j_database():
    #        print(f"Failed to create database {server.database}")
    #        server.close()
    #        return
    # Wait for 3s SM3 to be available
    #time.sleep(3)
    #server.close()
    server = LocalServer()
    # Verify the existence of the default database based on neo4j definition
    if server.check_sm3_database_existence():
        # Loading of indexes and loafing of data
        server.pre_ingest()
        file_list = config['files']
        for file in file_list:
            #print(file)
            server.load_file(file)
        server.post_ingest()

        print("Data has been inserted into Neo4j database")
    server.run_db_test()
    server.close()

if __name__ == "__main__":
    main()
