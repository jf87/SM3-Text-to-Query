import csv
import logging

import pymongo
import argparse
import time
from tqdm import tqdm
import yaml

"""
This code is adapted from the pyingest library. Mainly structural elements were reused for the mongodb implimentation.
Source: https://github.com/neo4j-field/pyingest
Original License: Apache-2.0 license

Modifications made for the Synthea healthcare data ingestion into Mongodb. 
- Creation of the SM3 MongoDB database 
- Definition of collections in line with Synthea CSV data
"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = dict()

class LocalServer(object):

    def __init__(self):
        # Static definition of variables for computation of connection:
        DB_USER = 'sm3'
        DB_PASSWORD = 'sm3'
        MONGODB_HOST = 'sm3_mongodb'
        MONGODB_PORT = 27017
        #self.client = pymongo.MongoClient(config['server_uri'])
        self.client = pymongo.MongoClient(
            host=MONGODB_HOST,
            port=MONGODB_PORT,
            username=DB_USER,
            password=DB_PASSWORD,
            authSource='admin',
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000
        )
        self.database_name = {}
        self.database = config['database'] if 'database' in config else None
        if self.database is not None:
            self.database_name = self.database
        self.basepath = config['basepath'] if 'basepath' in config else None
        self.collection_names = [
            "organizations",
            "payers",
            "patients",
            "encounters",
            "procedures",
            "providers",
            "allergies",
            "careplans",
            "claims",
            "claims_transactions",
            "conditions",
            "devices",
            "imaging_studies",
            "immunizations",
            "medications",
            "observations",
            "payer_transitions",
            "supplies",
            "patient_expenses",
        ]

    def check_sm3_database_existence(self):
        try:
            list_databases = self.client.list_database_names()
            return self.database_name in list_databases
        except Exception as e:
            print(f"Error checking the SM3 MongoDB database existence: {str(e)}")
            return False
    def check_sm3_collections_existence(self):
        try:
            sm3_database = self.client[f'{self.database_name}']
            list_collection_names = sm3_database.list_collection_names()
            for collection_name in list_collection_names:
                if not collection_name in self.collection_names:
                    return False
            return True
        except Exception as e:
            print(f"Error while checking the existence of data: {str(e)}")

    def create_sm3_database_new(self):
        try:
            self.database = self.client[f'{self.database_name}']
            print('sm3 created')
            # Insert regular data
            for collection_name in self.collection_names:

                self.database.create_collection(f'{collection_name}')
                if collection_name == 'patients':
                    self.import_csv(self.basepath + 'patients.csv', 'patients', self.map_patients)
                elif collection_name == 'organizations':
                    self.import_csv(self.basepath + 'organizations.csv', 'organizations', self.map_organizations)
                elif collection_name == 'providers':
                    self.import_csv(self.basepath + 'providers.csv', 'providers', self.map_providers)
                elif collection_name == 'payers':
                    self.import_csv(self.basepath + 'payers.csv', 'payers', self.map_payers)
                elif collection_name == 'encounters':
                    self.import_csv(self.basepath + 'encounters.csv', 'encounters', self.map_encounters)
                elif collection_name == 'conditions':
                    self.import_csv(self.basepath + 'conditions.csv', 'conditions', self.map_conditions)
                elif collection_name == 'allergies':
                    self.import_csv(self.basepath + 'allergies.csv', 'allergies', self.map_allergies)
                elif collection_name == 'medications':
                    self.import_csv(self.basepath + 'medications.csv', 'medications', self.map_medications)
                elif collection_name == 'careplans':
                    self.import_csv(self.basepath + 'careplans.csv', 'careplans', self.map_careplans)
                elif collection_name == 'observations':
                    self.import_csv(self.basepath + 'observations.csv', 'observations', self.map_observations)
                elif collection_name == 'procedures':
                    self.import_csv(self.basepath + 'procedures.csv', 'procedures', self.map_procedures)
                elif collection_name == 'immunizations':
                    self.import_csv(self.basepath + 'immunizations.csv', 'immunizations', self.map_immunizations)
                elif collection_name == 'imaging_studies':
                    self.import_csv(self.basepath + 'imaging_studies.csv', 'imaging_studies', self.map_imaging_studies)
                elif collection_name == 'devices':
                    self.import_csv(self.basepath + 'devices.csv', 'devices', self.map_devices)
                elif collection_name == 'supplies':
                    self.import_csv(self.basepath + 'supplies.csv', 'supplies', self.map_supplies)
                elif collection_name == 'claims':
                    self.import_csv(self.basepath + 'claims.csv', 'claims', self.map_claims)
                elif collection_name == 'claims_transactions':
                    self.import_csv(self.basepath + 'claims_transactions.csv', 'claims_transactions',
                                    self.map_claims_transactions)
                elif collection_name == 'payer_transitions':
                    self.import_csv(self.basepath + 'payer_transitions.csv', 'payer_transitions',
                                    self.map_payer_transitions)
                elif collection_name == 'patient_expenses':
                    self.import_csv(self.basepath + 'patient_expenses.csv', 'patient_expenses',
                                    self.map_patient_expenses)

            print(f"Created SM3 database: {self.database_name}")
            self.embedding_update()
            return True
        except Exception as e:
            print(f"Error creating database: {str(e)}")
            return False

    # Removes collections, which should not be in the sm3 database and creates the defined collections based on the definition above.
    def create_sm3_collections_corrected(self):
        # get all the collections associated to the sm3 database
        sm3_database = self.client[f'{self.database_name}']
        list_collection_names = sm3_database.list_collection_names()
        # Insert regular data
        for collection_name in list_collection_names:
            if collection_name in self.collection_names:
                # Check if there are any entries in the collection
                current_collection = sm3_database[f'{collection_name}']
                if not current_collection.count_documents({}) > 0:
                    # No entries defined hence definition of collection as new
                    # Drop current version and import most up to date data
                    self.database.drop_collection()
                    # Distinction of the different collections:
                    if collection_name == 'patients':
                        self.import_csv(self.basepath + 'patients.csv', 'patients', self.map_patients)
                    elif collection_name =='organizations':
                        self.import_csv(self.basepath + 'organizations.csv', 'organizations', self.map_organizations)
                    elif collection_name == 'providers':
                        self.import_csv(self.basepath + 'providers.csv', 'providers', self.map_providers)
                    elif collection_name == 'payers':
                        self.import_csv(self.basepath + 'payers.csv', 'payers', self.map_payers)
                    elif collection_name == 'encounters':
                        self.import_csv(self.basepath + 'encounters.csv', 'encounters', self.map_encounters)
                    elif collection_name == 'conditions':
                        self.import_csv(self.basepath + 'conditions.csv', 'conditions', self.map_conditions)
                    elif collection_name == 'allergies':
                        self.import_csv(self.basepath + 'allergies.csv', 'allergies', self.map_allergies)
                    elif collection_name == 'medications':
                        self.import_csv(self.basepath + 'medications.csv', 'medications', self.map_medications)
                    elif collection_name == 'careplans':
                        self.import_csv(self.basepath + 'careplans.csv', 'careplans', self.map_careplans)
                    elif collection_name == 'observations':
                        self.import_csv(self.basepath + 'observations.csv', 'observations', self.map_observations)
                    elif collection_name == 'procedures':
                        self.import_csv(self.basepath + 'procedures.csv', 'procedures', self.map_procedures)
                    elif collection_name == 'immunizations':
                        self.import_csv(self.basepath + 'immunizations.csv', 'immunizations', self.map_immunizations)
                    elif collection_name == 'imaging_studies':
                        self.import_csv(self.basepath + 'imaging_studies.csv', 'imaging_studies', self.map_imaging_studies)
                    elif collection_name == 'devices':
                        self.import_csv(self.basepath + 'devices.csv', 'devices', self.map_devices)
                    elif collection_name == 'supplies':
                        self.import_csv(self.basepath + 'supplies.csv', 'supplies', self.map_supplies)
                    elif collection_name == 'claims':
                        self.import_csv(self.basepath + 'claims.csv', 'claims', self.map_claims)
                    elif collection_name == 'claims_transactions':
                        self.import_csv(self.basepath + 'claims_transactions.csv', 'claims_transactions', self.map_claims_transactions)
                    elif collection_name == 'payer_transitions':
                        self.import_csv(self.basepath + 'payer_transitions.csv', 'payer_transitions', self.map_payer_transitions)
                    elif collection_name == 'patient_expenses':
                        self.import_csv(self.basepath + 'patient_expenses.csv', 'patient_expenses', self.map_patient_expenses)
            else:
                sm3_database.drop_collection(collection_name)
        self.embedding_update()

    # Embedding helper functions
    def embedding_update(self):
        print(f"\n{'=' * 80}")
        print(f"Starting to embed objects in patient documents...")
        print(f"{'=' * 80}")
        start_time = time.time()
        self.processed = 0
        self.embed_encounters_in_patients()
        self.embed_observations_in_patients()
        self.embed_conditions_in_patients()
        self.embed_allergies_in_patients()
        self.embed_medications_in_patients()
        self.embed_careplans_in_patients()
        self.embed_procedures_in_patients()
        self.embed_immunizations_in_patients()
        self.embed_imaging_studies_in_patients()
        self.embed_devices_in_patients()
        self.embed_supplies_in_patients()
        self.embed_claims_in_patients()
        self.embed_claims_transactions_in_patients()
        self.embed_payer_transitions_in_patients()

        elapsed_time = time.time() - start_time
        print(f"\n{'=' * 80}")
        print(f"Completed embedding {self.processed:,} objects into patients")
        print(f"Total time: {elapsed_time:.2f} seconds")
        print(f"Average speed: {self.processed / elapsed_time:.2f} objects/second")
        print(f"{'=' * 80}\n")





    def embed_encounters_in_patients(self):
        total_ = self.client[f'{self.database_name}'].encounters.count_documents({})
        with tqdm(total=total_, desc="Processing encounters",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for encounter in self.client[f'{self.database_name}'].encounters.find():
                patient_id = encounter["PATIENT_REF"]
                del encounter["PATIENT_REF"]

                # Update patient document
                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id},
                    {"$push": {"ENCOUNTERS": encounter}}
                )

                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].encounters.drop()

    def embed_observations_in_patients(self):
        total_ = self.client[f'{self.database_name}'].observations.count_documents({})
        with tqdm(total=total_, desc="Processing observations",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for observation in self.client[f'{self.database_name}'].observations.find():
                patient_id = observation["PATIENT_REF"]
                encounter_id = observation["ENCOUNTER_REF"]
                del observation["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the observation document
                del observation["ENCOUNTER_REF"]
                # Update patient document
                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                    {"$push": {"ENCOUNTERS.$.OBSERVATIONS": observation}}
                )

                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].observations.drop()

    def embed_conditions_in_patients(self):
        total_ = self.client[f'{self.database_name}'].conditions.count_documents({})
        with tqdm(total=total_, desc="Processing conditions",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for condition in self.client[f'{self.database_name}'].conditions.find():
                patient_id = condition["PATIENT_REF"]
                encounter_id = condition["ENCOUNTER_REF"]
                del condition["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the document
                del condition["ENCOUNTER_REF"]
                # Update patient document
                result = self.client[f'{self.database_name}'].patients.update_one(
                {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                {"$push": {"ENCOUNTERS.$.CONDITIONS": condition}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].conditions.drop()

    def embed_allergies_in_patients(self):
        total_ = self.client[f'{self.database_name}'].allergies.count_documents({})
        with tqdm(total=total_, desc="Processing allergies",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for allergy in self.client[f'{self.database_name}'].allergies.find():
                patient_id = allergy["PATIENT_REF"]
                encounter_id = allergy["ENCOUNTER_REF"]
                del allergy["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the document
                del allergy["ENCOUNTER_REF"]  # Remove the "ENCOUNTER_ID" field from the document

                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                    {"$push": {"ENCOUNTERS.$.ALLERGIES": allergy}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].allergies.drop()

    def embed_medications_in_patients(self):
        total_ = self.client[f'{self.database_name}'].medications.count_documents({})
        with tqdm(total=total_, desc="Processing medications",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for medication in self.client[f'{self.database_name}'].medications.find():
                patient_id = medication["PATIENT_REF"]
                encounter_id = medication["ENCOUNTER_REF"]
                del medication["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the document
                del medication["ENCOUNTER_REF"]  # Remove the "ENCOUNTER_ID" field from the document

                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                    {"$push": {"ENCOUNTERS.$.MEDICATIONS": medication}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].medications.drop()

    def embed_careplans_in_patients(self):
        total_ = self.client[f'{self.database_name}'].careplans.count_documents({})
        with tqdm(total=total_, desc="Processing careplans",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for careplan in self.client[f'{self.database_name}'].medications.find():
                patient_id = careplan["PATIENT_REF"]
                encounter_id = careplan["ENCOUNTER_REF"]
                del careplan["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the document
                del careplan["ENCOUNTER_REF"]  # Remove the "ENCOUNTER_ID" field from the document

                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                    {"$push": {"ENCOUNTERS.$.CAREPLANS": careplan}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].careplans.drop()

    def embed_procedures_in_patients(self):
        total_ = self.client[f'{self.database_name}'].procedures.count_documents({})
        with tqdm(total=total_, desc="Processing procedures",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for procedure in self.client[f'{self.database_name}'].procedures.find():
                patient_id = procedure["PATIENT_REF"]
                encounter_id = procedure["ENCOUNTER_REF"]
                del procedure["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the document
                del procedure["ENCOUNTER_REF"]  # Remove the "ENCOUNTER_ID" field from the document

                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                    {"$push": {"ENCOUNTERS.$.PROCEDURES": procedure}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].procedures.drop()

    def embed_immunizations_in_patients(self):
        total_ = self.client[f'{self.database_name}'].immunizations.count_documents({})
        with tqdm(total=total_, desc="Processing immunizations",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for immunization in self.client[f'{self.database_name}'].immunizations.find():
                patient_id = immunization["PATIENT_REF"]
                encounter_id = immunization["ENCOUNTER_REF"]
                del immunization["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the document
                del immunization["ENCOUNTER_REF"]  # Remove the "ENCOUNTER_ID" field from the document

                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                    {"$push": {"ENCOUNTERS.$.IMMUNIZATIONS": immunization}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].immunizations.drop()

    def embed_imaging_studies_in_patients(self):
        total_ = self.client[f'{self.database_name}'].imaging_studies.count_documents({})
        with tqdm(total=total_, desc="Processing imaging_studies",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for imaging_study in self.client[f'{self.database_name}'].imaging_studies.find():
                patient_id = imaging_study["PATIENT_REF"]
                encounter_id = imaging_study["ENCOUNTER_REF"]
                del imaging_study["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the document
                del imaging_study["ENCOUNTER_REF"]  # Remove the "ENCOUNTER_ID" field from the document

                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                    {"$push": {"ENCOUNTERS.$.IMAGING_STUDIES": imaging_study}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].imaging_studies.drop()

    def embed_devices_in_patients(self):
        total_ = self.client[f'{self.database_name}'].devices.count_documents({})
        with tqdm(total=total_, desc="Processing devices",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for device in self.client[f'{self.database_name}'].devices.find():
                patient_id = device["PATIENT_REF"]
                encounter_id = device["ENCOUNTER_REF"]
                del device["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the document
                del device["ENCOUNTER_REF"]  # Remove the "ENCOUNTER_ID" field from the document

                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                    {"$push": {"ENCOUNTERS.$.DEVICES": device}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].devices.drop()

    def embed_supplies_in_patients(self):
        total_ = self.client[f'{self.database_name}'].supplies.count_documents({})
        with tqdm(total=total_, desc="Processing supplies",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for supply in self.client[f'{self.database_name}'].supplies.find():
                patient_id = supply["PATIENT_REF"]
                encounter_id = supply["ENCOUNTER_REF"]
                del supply["PATIENT_REF"]  # Remove the "PATIENT_ID" field from the document
                del supply["ENCOUNTER_REF"]  # Remove the "ENCOUNTER_ID" field from the document

                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "ENCOUNTERS.ENCOUNTER_ID": encounter_id},
                    {"$push": {"ENCOUNTERS.$.SUPPLIES": supply}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].supplies.drop()

    def embed_claims_in_patients(self):
        total_ = self.client[f'{self.database_name}'].claims.count_documents({})
        with tqdm(total=total_, desc="Processing claims",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for claim in self.client[f'{self.database_name}'].claims.find():
                patient_id = claim["PATIENT_REF"]
                del claim["PATIENT_REF"]  # Remove the "PATIENT" field from the document
                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id},
                    {"$push": {"CLAIMS": claim}}
                )

                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].claims.drop()

    def embed_claims_transactions_in_patients(self):
        total_ = self.client[f'{self.database_name}'].claims_transactions.count_documents({})
        with tqdm(total=total_, desc="Processing claims_transactions",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for claim_transaction in self.client[f'{self.database_name}'].claims_transactions.find():
                patient_id = claim_transaction["PATIENT_REF"]
                claim_id = claim_transaction["CLAIM_REF"]
                del claim_transaction["PATIENT_REF"]  # Remove the "PATIENT" field from the document
                del claim_transaction["CLAIM_REF"]  # Remove the "PATIENT" field from the document

                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id, "CLAIMS.CLAIM_ID": claim_id},
                    {"$push": {"CLAIMS.$.CLAIM_TRANSACTIONS": claim_transaction}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].claims_transactions.drop()

    def embed_payer_transitions_in_patients(self):
        total_ = self.client[f'{self.database_name}'].payer_transitions.count_documents({})
        with tqdm(total=total_, desc="Processing payer_transitions",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for payer_transition in self.client[f'{self.database_name}'].payer_transitions.find():
                patient_id = payer_transition["PATIENT_REF"]
                del payer_transition["PATIENT_REF"]  # Remove the "PATIENT" field from the document
                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id},
                    {"$push": {"PAYER_TRANSITIONS": payer_transition}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].payer_transitions.drop()

    def embed_patient_expenses_in_patients(self):
        total_ = self.client[f'{self.database_name}'].patient_expenses.count_documents({})
        with tqdm(total=total_, desc="Processing patient_expenses",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            start_time = time.time()
            processed = 0
            for expense in self.client[f'{self.database_name}'].patient_expenses.find():
                patient_id = expense["PATIENT_REF"]
                del expense["PATIENT_REF"]  # Remove the "PATIENT" field from the document
                result = self.client[f'{self.database_name}'].patients.update_one(
                    {"PATIENT_ID": patient_id},
                    {"$push": {"EXPENSES": expense}}
                )
                # Update progress
                processed += 1
                if processed % 100 == 0:  # Log every 100 records
                    pbar.set_postfix({
                        "Last Patient": patient_id[:8] + "...",
                        "Modified": result.modified_count
                    })
                pbar.update(1)
            self.processed += processed
        self.client[f'{self.database_name}'].patient_expenses.drop()

    def run_mongodb_test(self):
        try:
            db = self.client[f'{self.database_name}']
            print("\nRunning MongoDB database tests...")
            print("=" * 80)

            # Test query for ROYAL OF FAIRHAVEN NURSING CENTER
            pipeline = [
                {
                    "$match": {
                        "NAME": "ROYAL OF FAIRHAVEN NURSING CENTER"
                    }
                },
                {
                    "$lookup": {
                        "from": "patients",
                        "localField": "ORGANIZATION_ID",
                        "foreignField": "ENCOUNTERS.ORGANIZATION_REF",
                        "as": "op"
                    }
                },
                {
                    "$unwind": "$op"
                },
                {
                    "$unwind": "$op.ENCOUNTERS"
                },
                {
                    "$match": {
                        "NAME": "ROYAL OF FAIRHAVEN NURSING CENTER"
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "first": "$op.FIRST",
                            "last": "$op.LAST"
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "first": "$_id.first",
                        "last": "$_id.last"
                    }
                }
            ]

            print("Running test query:")
            print(f"db.organizations.aggregate({pipeline})")
            print("\nResults:")

            results = list(db.organizations.aggregate(pipeline))

            # Print results in a formatted way
            for result in results:
                print(f"First Name: {result['first']}, Last Name: {result['last']}")

            # Check specific test case
            expected_result = {'first': 'Glendora96', 'last': 'Tillman293'}
            if any(r['first'] == expected_result['first'] and r['last'] == expected_result['last'] for r in results):
                print("\n✅ Test passed: Found expected patient Glendora96 Tillman293")
            else:
                print("\n❌ Test failed: Could not find expected patient Glendora96 Tillman293")

            # Print some basic statistics
            print("\nQuery Statistics:")
            print(f"Total distinct patients: {len(results)}")

        except Exception as e:
            print(f"\n❌ Test error occurred: {str(e)}")
        finally:
            print("=" * 80)

    # Mapping functions for each CSV file
    @staticmethod
    def map_patients(row):
        return {
            "PATIENT_ID": row["Id"],
            "BIRTHDATE": row["BIRTHDATE"],
            "DEATHDATE": row["DEATHDATE"],
            "SSN": row["SSN"],
            "DRIVERS": row["DRIVERS"],
            "PASSPORT": row["PASSPORT"],
            "PREFIX": row["PREFIX"],
            "FIRST": row["FIRST"],
            "LAST": row["LAST"],
            "SUFFIX": row["SUFFIX"],
            "MAIDEN": row["MAIDEN"],
            "MARITAL": row["MARITAL"],
            "RACE": row["RACE"],
            "ETHNICITY": row["ETHNICITY"],
            "GENDER": row["GENDER"],
            "BIRTHPLACE": row["BIRTHPLACE"],
            "ADDRESS": row["ADDRESS"],
            "CITY": row["CITY"],
            "STATE": row["STATE"],
            "COUNTY": row["COUNTY"],
            "FIPS": float(row["FIPS"]) if row["FIPS"] else None,
            "ZIP": row["ZIP"],
            "LAT": float(row["LAT"]),
            "LON": float(row["LON"]),
            "HEALTHCARE_EXPENSES": float(row["HEALTHCARE_EXPENSES"]),
            "HEALTHCARE_COVERAGE": float(row["HEALTHCARE_COVERAGE"]),
            "INCOME": int(row["INCOME"])
        }

    @staticmethod
    def map_encounters(row):
        return {
            "ENCOUNTER_ID": row["Id"],
            "START": row["START"],
            "STOP": row["STOP"],
            "PATIENT_REF": row["PATIENT"],
            "ORGANIZATION_REF": row["ORGANIZATION"],
            "PROVIDER_REF": row["PROVIDER"],
            "PAYER_REF": row["PAYER"],
            "ENCOUNTER_CLASS": row["ENCOUNTERCLASS"],
            "CODE": int(row["CODE"]),
            "DESCRIPTION": row["DESCRIPTION"],
            "BASE_ENCOUNTER_COST": float(row["BASE_ENCOUNTER_COST"]),
            "TOTAL_CLAIM_COST": float(row["TOTAL_CLAIM_COST"]),
            "PAYER_COVERAGE": float(row["PAYER_COVERAGE"]),
            "REASON_CODE": int(row["REASONCODE"]) if row["REASONCODE"] else None,
            "REASON_DESCRIPTION": row["REASONDESCRIPTION"]
        }

    @staticmethod
    def map_conditions(row):
        return {
            "START": row["START"],
            "STOP": row["STOP"],
            "PATIENT_REF": row["PATIENT"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "CODE": int(row["CODE"]),
            "DESCRIPTION": row["DESCRIPTION"]
        }

    @staticmethod
    def map_allergies(row):
        return {
            "START": row["START"],
            "STOP": row["STOP"],
            "PATIENT_REF": row["PATIENT"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "CODE": int(row["CODE"]),
            "SYSTEM": row["SYSTEM"],
            "DESCRIPTION": row["DESCRIPTION"],
            "TYPE": row["TYPE"],
            "CATEGORY": row["CATEGORY"],
            "REACTION_1": int(row["REACTION1"]) if row["REACTION1"] else None,
            "DESCRIPTION_1": row["DESCRIPTION1"],
            "SEVERITY_1": row["SEVERITY1"],
            "REACTION_2": int(row["REACTION2"]) if row["REACTION2"] else None,
            "DESCRIPTION_2": row["DESCRIPTION2"],
            "SEVERITY_2": row["SEVERITY2"]
        }

    @staticmethod
    def map_medications(row):
        return {
            "START": row["START"],
            "STOP": row["STOP"],
            "PATIENT_REF": row["PATIENT"],
            "PAYER_REF": row["PAYER"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "CODE": int(row["CODE"]),
            "DESCRIPTION": row["DESCRIPTION"],
            "BASE_COST": float(row["BASE_COST"]),
            "PAYER_COVERAGE": float(row["PAYER_COVERAGE"]),
            "DISPENSES": int(row["DISPENSES"]),
            "TOTAL_COST": float(row["TOTALCOST"]),
            "REASON_CODE": int(row["REASONCODE"]) if row["REASONCODE"] else None,
            "REASON_DESCRIPTION": row["REASONDESCRIPTION"]
        }

    @staticmethod
    def map_careplans(row):
        return {
            "CAREPLAN_ID": row["Id"],
            "START": row["START"],
            "STOP": row["STOP"],
            "PATIENT_REF": row["PATIENT"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "CODE": int(row["CODE"]),
            "DESCRIPTION": row["DESCRIPTION"],
            "REASON_CODE": int(row["REASONCODE"]) if row["REASONCODE"] else None,
            "REASON_DESCRIPTION": row["REASONDESCRIPTION"]
        }

    @staticmethod
    def map_observations(row):
        return {
            "DATE": row["DATE"],
            "PATIENT_REF": row["PATIENT"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "CATEGORY": row["CATEGORY"],
            "CODE": row["CODE"],
            "DESCRIPTION": row["DESCRIPTION"],
            "VALUE": row["VALUE"],
            "UNITS": row["UNITS"],
            "TYPE": row["TYPE"]
        }

    @staticmethod
    def map_procedures(row):
        return {
            "START": row["START"],
            "STOP": row["STOP"],
            "PATIENT_REF": row["PATIENT"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "CODE": int(row["CODE"]),
            "DESCRIPTION": row["DESCRIPTION"],
            "BASE_COST": float(row["BASE_COST"]),
            "REASON_CODE": int(row["REASONCODE"]) if row["REASONCODE"] else None,
            "REASON_DESCRIPTION": row["REASONDESCRIPTION"]
        }

    @staticmethod
    def map_immunizations(row):
        return {
            "DATE": row["DATE"],
            "PATIENT_REF": row["PATIENT"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "CODE": int(row["CODE"]),
            "DESCRIPTION": row["DESCRIPTION"],
            "BASE_COST": float(row["BASE_COST"])
        }

    @staticmethod
    def map_imaging_studies(row):
        return {
            "IMAGING_STUDY_ID": row["Id"],
            "DATE": row["DATE"],
            "PATIENT_REF": row["PATIENT"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "SERIES_UID": row["SERIES_UID"],
            "BODYSITE_CODE": int(row["BODYSITE_CODE"]),
            "BODYSITE_DESCRIPTION": row["BODYSITE_DESCRIPTION"],
            "MODALITY_CODE": row["MODALITY_CODE"],
            "MODALITY_DESCRIPTION": row["MODALITY_DESCRIPTION"],
            "INSTANCE_UID": row["INSTANCE_UID"],
            "SOP_CODE": row["SOP_CODE"],
            "SOP_DESCRIPTION": row["SOP_DESCRIPTION"],
            "PROCEDURE_CODE": int(row["PROCEDURE_CODE"])
        }

    @staticmethod
    def map_devices(row):
        return {
            "START": row["START"],
            "STOP": row["STOP"],
            "PATIENT_REF": row["PATIENT"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "CODE": int(row["CODE"]),
            "DESCRIPTION": row["DESCRIPTION"],
            "UDI": row["UDI"]
        }

    @staticmethod
    def map_supplies(row):
        return {
            "DATE": row["DATE"],
            "PATIENT_REF": row["PATIENT"],
            "ENCOUNTER_REF": row["ENCOUNTER"],
            "CODE": int(row["CODE"]),
            "DESCRIPTION": row["DESCRIPTION"],
            "QUANTITY": int(row["QUANTITY"])
        }

    @staticmethod
    def map_claims(row):
        return {
            "CLAIM_ID": row["Id"],
            "PATIENT_REF": row["PATIENTID"],
            "PROVIDER_REF": row["PROVIDERID"],
            "PRIMARY_PATIENT_INSURANCE_REF": row["PRIMARYPATIENTINSURANCEID"],
            "SECONDARY_PATIENT_INSURANCE_REF": row["SECONDARYPATIENTINSURANCEID"],
            "DEPARTMENT_ID": int(row["DEPARTMENTID"]),
            "PATIENT_DEPARTMENT_ID": int(row["PATIENTDEPARTMENTID"]),
            "DIAGNOSIS_1": int(row["DIAGNOSIS1"]) if row["DIAGNOSIS1"] else None,
            "DIAGNOSIS_2": int(row["DIAGNOSIS2"]) if row["DIAGNOSIS2"] else None,
            "DIAGNOSIS_3": int(row["DIAGNOSIS3"]) if row["DIAGNOSIS3"] else None,
            "DIAGNOSIS_4": int(row["DIAGNOSIS4"]) if row["DIAGNOSIS4"] else None,
            "DIAGNOSIS_5": int(row["DIAGNOSIS5"]) if row["DIAGNOSIS5"] else None,
            "DIAGNOSIS_6": int(row["DIAGNOSIS6"]) if row["DIAGNOSIS6"] else None,
            "DIAGNOSIS_7": int(row["DIAGNOSIS7"]) if row["DIAGNOSIS7"] else None,
            "DIAGNOSIS_8": int(row["DIAGNOSIS8"]) if row["DIAGNOSIS8"] else None,
            "REFERRING_PROVIDER_REF": row["REFERRINGPROVIDERID"],
            "APPOINTMENT_REF": row["APPOINTMENTID"],
            "CURRENT_ILLNESS_DATE": row["CURRENTILLNESSDATE"],
            "SERVICE_DATE": row["SERVICEDATE"],
            "SUPERVISING_PROVIDER_REF": row["SUPERVISINGPROVIDERID"],
            "STATUS_1": row["STATUS1"],
            "STATUS_2": row["STATUS2"],
            "STATUS_P": row["STATUSP"],
            "OUTSTANDING_1": row["OUTSTANDING1"],
            "OUTSTANDING_2": row["OUTSTANDING2"],
            "OUTSTANDING_P": row["OUTSTANDINGP"],
            "LAST_BILLED_DATE_1": row["LASTBILLEDDATE1"],
            "LAST_BILLED_DATE_2": row["LASTBILLEDDATE2"],
            "LAST_BILLED_DATE_P": row["LASTBILLEDDATEP"],
            "HEALTHCARE_CLAIM_TYPE_ID_1": int(row["HEALTHCARECLAIMTYPEID1"]) if row["HEALTHCARECLAIMTYPEID1"] else None,
            "HEALTHCARE_CLAIM_TYPE_ID_2": int(row["HEALTHCARECLAIMTYPEID2"]) if row["HEALTHCARECLAIMTYPEID2"] else None
        }

    @staticmethod
    def map_claims_transactions(row):
        return {
            "CLAIM_TRANSACTION_ID": row["ID"],
            "CLAIM_REF": row["CLAIMID"],
            "CHARGE_ID": float(row["CHARGEID"]),
            "PATIENT_REF": row["PATIENTID"],
            "TYPE": row["TYPE"],
            "AMOUNT": row["AMOUNT"],
            "METHOD": row["METHOD"],
            "FROMDATE": row["FROMDATE"],
            "TODATE": row["TODATE"],
            "PLACE_OF_SERVICE": row["PLACEOFSERVICE"],
            "PROCEDURE_CODE": row["PROCEDURECODE"],
            "MODIFIER_1": row["MODIFIER1"],
            "MODIFIER_2": row["MODIFIER2"],
            "DIAGNOSIS_REF_1": row["DIAGNOSISREF1"],
            "DIAGNOSIS_REF_2": row["DIAGNOSISREF2"],
            "DIAGNOSIS_REF_3": row["DIAGNOSISREF3"],
            "DIAGNOSIS_REF_4": row["DIAGNOSISREF4"],
            "UNITS": int(row["UNITS"]),
            "DEPARTMENT_ID": row["DEPARTMENTID"],
            "NOTES": row["NOTES"],
            "UNIT_AMOUNT": row["UNITAMOUNT"],
            "TRANSFER_OUT_ID": row["TRANSFEROUTID"],
            "TRANSFER_TYPE": row["TRANSFERTYPE"],
            "PAYMENTS": row["PAYMENTS"],
            "ADJUSTMENTS": row["ADJUSTMENTS"],
            "TRANSFERS": row["TRANSFERS"],
            "OUTSTANDING": row["OUTSTANDING"],
            "APPOINTMENT_REF": row["APPOINTMENTID"],
            "LINE_NOTE": row["LINENOTE"],
            "PATIENT_INSURANCE_REF": row["PATIENTINSURANCEID"],
            "FEE_SCHEDULEID": row["FEESCHEDULEID"],
            "PROVIDER_REF": row["PROVIDERID"],
            "SUPERVISING_PROVIDER_REF": row["SUPERVISINGPROVIDERID"]
        }

    @staticmethod
    def map_payer_transitions(row):
        return {
            "PATIENT_REF": row["PATIENT"],
            "MEMBER_ID": row["MEMBERID"],
            "START_DATE": row["START_DATE"],
            "END_DATE": row["END_DATE"],
            "PAYER_REF": row["PAYER"],
            "SECONDARY_PAYER_REF": row["SECONDARY_PAYER"],
            "PLAN_OWNERSHIP": row["PLAN_OWNERSHIP"],
            "OWNER_NAME": row["OWNER_NAME"]
        }

    @staticmethod
    def map_organizations(row):
        return {
            "ORGANIZATION_ID": row["Id"],
            "NAME": row["NAME"],
            "ADDRESS": row["ADDRESS"],
            "CITY": row["CITY"],
            "STATE": row["STATE"],
            "ZIP": row["ZIP"],
            "LAT": float(row["LAT"]),
            "LON": float(row["LON"]),
            "PHONE": row["PHONE"],
            "REVENUE": float(row["REVENUE"]),
            "UTILIZATION": int(row["UTILIZATION"])
        }

    @staticmethod
    def map_providers(row):
        return {
            "PROVIDER_ID": row["Id"],
            "ORGANIZATION_REF": row["ORGANIZATION"],
            "NAME": row["NAME"],
            "GENDER": row["GENDER"],
            "SPECIALITY": row["SPECIALITY"],
            "ADDRESS": row["ADDRESS"],
            "CITY": row["CITY"],
            "STATE": row["STATE"],
            "ZIP": row["ZIP"],
            "LAT": float(row["LAT"]),
            "LON": float(row["LON"]),
            "ENCOUNTERS": int(row["ENCOUNTERS"]),
            "PROCEDURES": int(row["PROCEDURES"])
        }

    @staticmethod
    def map_payers(row):
        return {
            "PAYER_ID": row["Id"],
            "NAME": row["NAME"],
            "OWNERSHIP": row["OWNERSHIP"],
            "AMOUNT_COVERED": float(row["AMOUNT_COVERED"]),
            "AMOUNT_UNCOVERED": float(row["AMOUNT_UNCOVERED"]),
            "REVENUE": float(row["REVENUE"]),
            "COVERED_ENCOUNTERS": int(row["COVERED_ENCOUNTERS"]),
            "UNCOVERED_ENCOUNTERS": int(row["UNCOVERED_ENCOUNTERS"]),
            "COVERED_MEDICATIONS": int(row["COVERED_MEDICATIONS"]),
            "UNCOVERED_MEDICATIONS": int(row["UNCOVERED_MEDICATIONS"]),
            "COVERED_PROCEDURES": int(row["COVERED_PROCEDURES"]),
            "UNCOVERED_PROCEDURES": int(row["UNCOVERED_PROCEDURES"]),
            "COVERED_IMMUNIZATIONS": int(row["COVERED_IMMUNIZATIONS"]),
            "UNCOVERED_IMMUNIZATIONS": int(row["UNCOVERED_IMMUNIZATIONS"]),
            "UNIQUE_CUSTOMERS": int(row["UNIQUE_CUSTOMERS"]),
            "QOLS_AVG": float(row["QOLS_AVG"]),
            "MEMBER_MONTHS": int(row["MEMBER_MONTHS"])
        }

    @staticmethod
    def map_patient_expenses(row):
        return {
            "PATIENT_REF": row["PATIENT_ID"],
            "YEAR": row["YEAR"],
            "PAYER_REF": row["PAYER_ID"],
            "HEALTHCARE_EXPENSES": float(row["HEALTHCARE_EXPENSES"]),
            "INSURANCE_COSTS": float(row["INSURANCE_COSTS"]),
            "COVERED_COSTS": float(row["COVERED_COSTS"])
        }

    def import_csv(self, file_path, collection_name, mapping_func):
        with open(file_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            data = [mapping_func(row) for row in csv_reader]
            self.database[collection_name].insert_many(data)

    def close(self):
        self.client.close()


# global defined functions and helper functions
def load_config(configuration):
    global config
    with open(configuration) as config_file:
        config = yaml.load(config_file, yaml.SafeLoader)

# TODO: definition of wait for db function, which waits and retires the connection
def wait_for_db(max_retries=60, delay_seconds=2):
    # Static definition of variables for computation of connection:
    DB_USER = 'sm3'
    DB_PASSWORD = 'sm3'
    MONGODB_HOST = 'sm3_mongodb'
    MONGODB_PORT = 27017
    for attempt in range(max_retries):
        try:
            #client = pymongo.MongoClient(
            #    f"mongodb://{DB_USER}:{DB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/admin",  # Using container name and credentials
            #    serverSelectionTimeoutMS=5000  # 5 second timeout
            #)
            client = pymongo.MongoClient(
                host=MONGODB_HOST,
                port=MONGODB_PORT,
                username=DB_USER,
                password=DB_PASSWORD,
                authSource='admin',
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS= 20000,
                socketTimeoutMS=20000
            )
            print("Waiting for server to respond...")
            time.sleep(2)  # Give MongoDB a moment to respond
            #client.admin.command('ismaster')
            client.admin.command('ping')
            print("MongoDB connection successful")
            return True
        except pymongo.errors.ConnectionFailure as e:
            print(f"Attempt {attempt + 1}/{max_retries} to connect to the MongoDB sm3 database failed")
            print(f"Error: {e}")
            time.sleep(delay_seconds)
            #raise
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} unexpected error:")
            print(f"Error: {e}")
            time.sleep(delay_seconds)
        finally:
            if 'client' in locals():
                client.close()
    raise Exception("Could not connect to the MongoDB sm3 database after 60 maximum retries")

def main():
    # Loading specific configuration from the config_mongodb.yml file
    configuration = '/app/config_mongodb.yml'
    load_config(configuration)
    # Wait for mongodb service to be ready before making any other computation:
    if not wait_for_db():
        logger.error("Failed to connect to database")
        return


    # Definition of specific Local Server object:
    server = LocalServer()
    # Check if the sm3 database exists for mongodb
    if server.check_sm3_database_existence():

        # Check if the respective collections are defined:
        if not server.check_sm3_collections_existence():
            server.create_sm3_collections_corrected()
            # Database exists but doesn't have all the collections as noted above

            # create missing collections:
            #print(server.client.list_database_names())
            #print(server.client[f'{server.database_name}'].list_collection_names())
            #print(server.check_sm3_database_existence())
            server.run_mongodb_test()
            print("SM3 data and database already exists in database. Import completed.")
            server.close()
            return
        else:

            print("SM3 data and database already exists in database. Import skipped.")
            #server.embedding_update()
            server.run_mongodb_test()
            server.close()
            return
    else:
        # Create the database from scratch
        if not server.create_sm3_database_new():
            print(f"Failed to create database {server.database}")
            server.close()
            return
        # both database and data have to be loaded::
        server.run_mongodb_test()

if __name__ == "__main__":
    main()