import csv
import os
import time
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


# Version 2: upgrade (custom data)
# TODO: enable the database to also have the remaining schemas ready
# TODO: change the respective call of import to capture all the csv files from the

# TODO: reconstruction of file for proper execution:

#   Connecting variables as environment variable
DB_USER = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'sm3')
DB_PASSWORD = os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'sm3')
DB_DATABASE = os.getenv('MONGO_INITDB_DATABASE', 'sm3')
MONGODB_HOST = "sm3_mongodb"
# Sidenote port changed for current run
MONGODB_PORT = "27017"
DATA_FOLDER = "/data/"
TABLES = ["organizations", "payers", "patients", "encounters", "procedures", "providers", "allergies",
              "careplans", "claims",
              "claims_transactions", "conditions", "devices", "imaging_studies", "immunizations", "medications",
              "observations",
              "payer_transitions", "supplies", "patient_expenses"]


def get_mongodb_client(max_retries=60, delay_seconds=1):
    """Create and return a MongoDB client with retry logic"""
    connection_string = f"mongodb://{DB_USER}:{DB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/admin"

    for attempt in range(max_retries):
        try:
            client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=30000,  # Increased timeout to 30 seconds
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                retryWrites=True,
                w='majority'
            )
            # Test the connection
            client.admin.command('ismaster')
            print("MongoDB connection successful")
            return client
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            if attempt == max_retries - 1:
                print(f"Failed to connect after {max_retries} attempts")
                raise
            print(f"Connection attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            time.sleep(delay_seconds)

# Definition of function to check connection
def wait_for_db(max_retries=60, delay_seconds=1):
    for attempt in range(max_retries):
        try:
            client = pymongo.MongoClient(
                f"mongodb://{DB_USER}:{DB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/admin",  # Using container name and credentials
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            #client.admin.command('ismaster')
            print("MongoDB connection successful")
            return True
        except pymongo.errors.ConnectionFailure as e:
            print(f"Attempt {attempt + 1}/{max_retries} to connect to the MongoDB sm3 database failed")
            print(f"Error: {e}")
            time.sleep(delay_seconds)
            raise

    raise Exception("Could not connect to the MongoDB sm3 database after 60 maximum retries")

# Creation of document store
# Step 1: Define clean state of the data -> delete all existing collections:
# For the deletion of existing document stores
def delete_db(db):
    # Get a list of all collection names in the database
    collection_names = db.list_collection_names()
    print(collection_names)
    # Iterate over the collection names and drop each collection
    for collection_name in collection_names:
        db[collection_name].drop()
    print("All collections deleted successfully.")

# For the creation of new document store of the data:
def import_csv(file_path, collection_name, mapping_func, db):
    with open(file_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        data = [mapping_func(row) for row in csv_reader]
        db[collection_name].insert_many(data)

# Definition of the respective mappings/schemas for the respective databases:
# Mapping functions for each CSV file
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
        "REASON_CODE": int(float(row["REASONCODE"])) if row["REASONCODE"] else None,
        "REASON_DESCRIPTION": row["REASONDESCRIPTION"]
    }

def map_conditions(row):
    return {
        "START": row["START"],
        "STOP": row["STOP"],
        "PATIENT_REF": row["PATIENT"],
        "ENCOUNTER_REF": row["ENCOUNTER"],
        "CODE": int(row["CODE"]),
        "DESCRIPTION": row["DESCRIPTION"]
    }

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
        "REACTION_1": int(float(row["REACTION1"])) if row["REACTION1"] else None,
        "DESCRIPTION_1": row["DESCRIPTION1"],
        "SEVERITY_1": row["SEVERITY1"],
        "REACTION_2": int(float(row["REACTION2"])) if row["REACTION2"] else None,
        "DESCRIPTION_2": row["DESCRIPTION2"],
        "SEVERITY_2": row["SEVERITY2"]
    }

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
        "REASON_CODE": int(float(row["REASONCODE"])) if row["REASONCODE"] else None,
        "REASON_DESCRIPTION": row["REASONDESCRIPTION"]
    }

def map_careplans(row):
    return {
        "CAREPLAN_ID": row["Id"],
        "START": row["START"],
        "STOP": row["STOP"],
        "PATIENT_REF": row["PATIENT"],
        "ENCOUNTER_REF": row["ENCOUNTER"],
        "CODE": int(row["CODE"]),
        "DESCRIPTION": row["DESCRIPTION"],
        "REASON_CODE": int(float(row["REASONCODE"])) if row["REASONCODE"] else None,
        "REASON_DESCRIPTION": row["REASONDESCRIPTION"]
    }

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

def map_procedures(row):
    return {
        "START": row["START"],
        "STOP": row["STOP"],
        "PATIENT_REF": row["PATIENT"],
        "ENCOUNTER_REF": row["ENCOUNTER"],
        "CODE": int(row["CODE"]),
        "DESCRIPTION": row["DESCRIPTION"],
        "BASE_COST": float(row["BASE_COST"]),
        "REASON_CODE": int(float(row["REASONCODE"])) if row["REASONCODE"] else None,
        "REASON_DESCRIPTION": row["REASONDESCRIPTION"]
    }

def map_immunizations(row):
    return {
        "DATE": row["DATE"],
        "PATIENT_REF": row["PATIENT"],
        "ENCOUNTER_REF": row["ENCOUNTER"],
        "CODE": int(row["CODE"]),
        "DESCRIPTION": row["DESCRIPTION"],
        "BASE_COST": float(row["BASE_COST"])
    }

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

def map_supplies(row):
    return {
        "DATE": row["DATE"],
        "PATIENT_REF": row["PATIENT"],
        "ENCOUNTER_REF": row["ENCOUNTER"],
        "CODE": int(row["CODE"]),
        "DESCRIPTION": row["DESCRIPTION"],
        "QUANTITY": int(row["QUANTITY"])
    }

def map_claims(row):
    return {
        "CLAIM_ID": row["Id"],
        "PATIENT_REF": row["PATIENTID"],
        "PROVIDER_REF": row["PROVIDERID"],
        "PRIMARY_PATIENT_INSURANCE_REF": row["PRIMARYPATIENTINSURANCEID"],
        "SECONDARY_PATIENT_INSURANCE_REF": row["SECONDARYPATIENTINSURANCEID"],
        "DEPARTMENT_ID": int(row["DEPARTMENTID"]),
        "PATIENT_DEPARTMENT_ID": int(row["PATIENTDEPARTMENTID"]),
        "DIAGNOSIS_1": int(float(row["DIAGNOSIS1"])) if row["DIAGNOSIS1"] else None,
        "DIAGNOSIS_2": int(float(row["DIAGNOSIS2"])) if row["DIAGNOSIS2"] else None,
        "DIAGNOSIS_3": int(float(row["DIAGNOSIS3"])) if row["DIAGNOSIS3"] else None,
        "DIAGNOSIS_4": int(float(row["DIAGNOSIS4"])) if row["DIAGNOSIS4"] else None,
        "DIAGNOSIS_5": int(float(row["DIAGNOSIS5"])) if row["DIAGNOSIS5"] else None,
        "DIAGNOSIS_6": int(float(row["DIAGNOSIS6"])) if row["DIAGNOSIS6"] else None,
        "DIAGNOSIS_7": int(float(row["DIAGNOSIS7"])) if row["DIAGNOSIS7"] else None,
        "DIAGNOSIS_8": int(float(row["DIAGNOSIS8"])) if row["DIAGNOSIS8"] else None,
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

def map_patient_expenses(row):
    return {
        "PATIENT_REF": row["PATIENT_ID"],
        "YEAR": row["YEAR"],
        "PAYER_REF": row["PAYER_ID"],
        "HEALTHCARE_EXPENSES": float(row["HEALTHCARE_EXPENSES"]),
        "INSURANCE_COSTS": float(row["INSURANCE_COSTS"]),
        "COVERED_COSTS": float(row["COVERED_COSTS"])
    }

# Embedding of underlying connection of documents:
def data_connection_embedding(db):
    # Create indexes for better query performance
    db.patients.create_index("PATIENT_ID")
    db.encounters.create_index("PATIENT_REF")
    db.claims.create_index("PATIENT_REF")

    # Instead of embedding everything, create separate collections with references

    # 1. Create a patient_encounters collection
    for encounter in db.encounters.find():
        patient_id = encounter["PATIENT_REF"]
        encounter_id = encounter["ENCOUNTER_ID"]

        # Create separate collections for encounter-related data
        encounter_data = {
            "PATIENT_REF": patient_id,
            "ENCOUNTER_ID": encounter_id,
            "ENCOUNTER_DATA": encounter,
            "OBSERVATIONS": [],
            "CONDITIONS": [],
            "ALLERGIES": [],
            "MEDICATIONS": [],
            "CAREPLANS": [],
            "PROCEDURES": [],
            "IMMUNIZATIONS": [],
            "IMAGING_STUDIES": [],
            "DEVICES": [],
            "SUPPLIES": []
        }

        db.patient_encounters.insert_one(encounter_data)

    # 2. Add related data to encounters
    collections_to_process = [
        (db.observations, "OBSERVATIONS"),
        (db.conditions, "CONDITIONS"),
        (db.allergies, "ALLERGIES"),
        (db.medications, "MEDICATIONS"),
        (db.careplans, "CAREPLANS"),
        (db.procedures, "PROCEDURES"),
        (db.immunizations, "IMMUNIZATIONS"),
        (db.imaging_studies, "IMAGING_STUDIES"),
        (db.devices, "DEVICES"),
        (db.supplies, "SUPPLIES")
    ]

    for collection, field_name in collections_to_process:
        for doc in collection.find():
            if "ENCOUNTER_REF" in doc:
                encounter_id = doc["ENCOUNTER_REF"]
                del doc["PATIENT_REF"]
                del doc["ENCOUNTER_REF"]

                db.patient_encounters.update_one(
                    {"ENCOUNTER_ID": encounter_id},
                    {"$push": {field_name: doc}},
                    upsert=True
                )

    # 3. Create separate collections for claims and related data
    db.patient_claims.create_index([("PATIENT_REF", 1), ("CLAIM_ID", 1)])

    for claim in db.claims.find():
        patient_id = claim["PATIENT_REF"]
        claim_id = claim["CLAIM_ID"]

        claim_data = {
            "PATIENT_REF": patient_id,
            "CLAIM_ID": claim_id,
            "CLAIM_DATA": claim,
            "TRANSACTIONS": []
        }

        db.patient_claims.insert_one(claim_data)

    # Add claim transactions
    for transaction in db.claims_transactions.find():
        claim_id = transaction["CLAIM_REF"]
        del transaction["PATIENT_REF"]
        del transaction["CLAIM_REF"]

        db.patient_claims.update_one(
            {"CLAIM_ID": claim_id},
            {"$push": {"TRANSACTIONS": transaction}}
        )

    # 4. Keep smaller collections as references in patient document
    for patient in db.patients.find():
        patient_id = patient["PATIENT_ID"]

        # Add references to encounters and claims
        encounter_refs = list(db.patient_encounters.find(
            {"PATIENT_REF": patient_id},
            {"_id": 0, "ENCOUNTER_ID": 1}
        ))

        claim_refs = list(db.patient_claims.find(
            {"PATIENT_REF": patient_id},
            {"_id": 0, "CLAIM_ID": 1}
        ))

        # Update patient with references
        db.patients.update_one(
            {"PATIENT_ID": patient_id},
            {"$set": {
                "ENCOUNTER_REFS": encounter_refs,
                "CLAIM_REFS": claim_refs,
                "PAYER_TRANSITIONS": list(db.payer_transitions.find(
                    {"PATIENT_REF": patient_id},
                    {"_id": 0, "PATIENT_REF": 0}
                )),
                "EXPENSES": list(db.patient_expenses.find(
                    {"PATIENT_REF": patient_id},
                    {"_id": 0, "PATIENT_REF": 0}
                ))
            }}
        )


# Add helper function to retrieve complete patient data
def get_complete_patient_data(db, patient_id):
    patient = db.patients.find_one({"PATIENT_ID": patient_id})
    if not patient:
        return None

    # Get referenced encounters
    encounters = list(db.patient_encounters.find({"PATIENT_REF": patient_id}))
    patient['ENCOUNTERS'] = encounters

    # Get referenced claims
    claims = list(db.patient_claims.find({"PATIENT_REF": patient_id}))
    patient['CLAIMS'] = claims

    return patient

def del_all_tables(db):
    db.patient_expenses.drop()  # Delete the patient_expenses collection
    db.payer_transitions.drop()  # Delete the payer_transitions collection
    db.claims_transactions.drop()  # Delete the claims_transactions collection
    db.claims.drop()  # Delete the claims collection
    db.supplies.drop()  # Delete the supplies collection
    db.devices.drop()  # Delete the devices collection
    db.imaging_studies.drop()  # Delete the imaging_studies collection
    db.immunizations.drop()  # Delete the immunizations collection
    db.procedures.drop()  # Delete the procedures collection
    db.observations.drop()  # Delete the observations collection
    db.careplans.drop()  # Delete the careplans collection
    db.allergies.drop()  # Delete the allergies collection
    db.conditions.drop()  # Delete the conditions collection
    db.encounters.drop()  # Delete the encounters collection
    db.medications.drop()  # Delete the encounters collection

def denormalized_test(db):
    # Denormalized version query
    denormalized_result = db.patients.find_one(
        {
            "ALLERGIES.DESCRIPTION": "Mold (organism)"
        },
        {
            "_id": 0,
            "ALLERGIES.$": 1
        }
    )

    if denormalized_result:
        allergy_code = denormalized_result['ALLERGIES'][0]['CODE']
        print("Denormalized version - Allergy Code:", allergy_code)
    else:
        print("Denormalized version - No matching allergy found.")

def normalized_test(db):
    normalized_result = db.allergies.find_one(
        {
            "DESCRIPTION": "Mold (organism)"
        },
        {
            "_id": 0,
            "CODE": 1
        }
    )

    if normalized_result:
        allergy_code = normalized_result['CODE']
        print("Normalized version - Allergy Code:", allergy_code)
    else:
        print("Normalized version - No matching allergy found.")

# TODO: 5
# Definition of main file, which will be executed upon createion of respective container:
def main():
    client = None
    try:
        # Wait for database to be ready
        if not wait_for_db():
            raise Exception("Database connection failed")

        # Get database client
        client = get_mongodb_client()
        db = client[DB_DATABASE]

        # Import data for each table
        for table in TABLES:
            try:
                filename = f'{DATA_FOLDER}{table}.csv'
                print(f"Processing {filename}...")
                mapping_func = globals()[f'map_{table}']

                # Read and import data in chunks to prevent memory issues
                chunk_size = 1000
                with open(filename, 'r') as file:
                    reader = csv.DictReader(file)
                    chunk = []

                    for row in reader:
                        chunk.append(mapping_func(row))
                        if len(chunk) >= chunk_size:
                            db[table].insert_many(chunk, ordered=False)
                            chunk = []

                    # Insert any remaining records
                    if chunk:
                        db[table].insert_many(chunk, ordered=False)

                print(f"Finished importing {table}")

            except Exception as e:
                print(f"Error processing table {table}: {str(e)}")
                continue

        # Create data embeddings with error handling
        try:
            print("Creating data embeddings...")
            data_connection_embedding(db)
            print("Data embeddings created successfully")
        except Exception as e:
            print(f"Error creating data embeddings: {str(e)}")
            raise

    except Exception as e:
        print(f'Error during mongodb database setup: {str(e)}')
        raise
    finally:
        if client:
            client.close()
        # remove existing data from the data store
        #delete_db(db)
        # add the currently referenced DATAFOLDER data to the database
        """ 
        print("Importing data...")
        for table in TABLES:
            filename = f'{DATA_FOLDER}{table}.csv'
            print(f"Processing {filename}...")
            mapping_func = globals()[f'map_{table}']
            import_csv(filename, table, mapping_func, db)
            print(f"Finished importing {table}")
        
        # Read all the csv data and compute the respective document store
        import_csv(DATA_FOLDER + 'patients.csv', 'patients', map_patients,db)
        import_csv(DATA_FOLDER + 'organizations.csv', 'organizations', map_organizations, db)
        import_csv(DATA_FOLDER + 'providers.csv', 'providers', map_providers, db)
        import_csv(DATA_FOLDER + 'payers.csv', 'payers', map_payers, db)
        import_csv(DATA_FOLDER + 'encounters.csv', 'encounters', map_encounters, db)
        import_csv(DATA_FOLDER + 'conditions.csv', 'conditions', map_conditions, db)
        import_csv(DATA_FOLDER + 'allergies.csv', 'allergies', map_allergies, db)
        import_csv(DATA_FOLDER + 'medications.csv', 'medications', map_medications, db)
        import_csv(DATA_FOLDER + 'careplans.csv', 'careplans', map_careplans, db)
        import_csv(DATA_FOLDER + 'observations.csv', 'observations', map_observations, db)
        import_csv(DATA_FOLDER + 'procedures.csv', 'procedures', map_procedures, db)
        import_csv(DATA_FOLDER + 'immunizations.csv', 'immunizations', map_immunizations, db)
        import_csv(DATA_FOLDER + 'imaging_studies.csv', 'imaging_studies', map_imaging_studies, db)
        import_csv(DATA_FOLDER + 'devices.csv', 'devices', map_devices, db)
        import_csv(DATA_FOLDER + 'supplies.csv', 'supplies', map_supplies, db)
        import_csv(DATA_FOLDER + 'claims.csv', 'claims', map_claims, db)
        import_csv(DATA_FOLDER + 'claims_transactions.csv', 'claims_transactions', map_claims_transactions, db)
        import_csv(DATA_FOLDER + 'payer_transitions.csv', 'payer_transitions', map_payer_transitions, db)
        import_csv(DATA_FOLDER + 'patient_expenses.csv', 'patient_expenses', map_patient_expenses, db)
       
        # Definition of the respective embedding:
        print("Creating data embeddings...")
        data_connection_embedding(db)
        print('placeholder for the respective schema creator')
         """


if __name__ == '__main__':
    main()






