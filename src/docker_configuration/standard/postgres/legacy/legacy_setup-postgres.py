# Imports of all the extentions
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Connection variables as environment variable
DB_HOST = os.getenv('DB_HOST', 'sm3_postgres')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'sm3')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'sm3')
DB_NAME = os.getenv('DB_NAME', 'sm3')

# Backoff for the database connection:
# Since the connection is not necessarily defined such
def wait_for_db(max_retries=60, delay_seconds=1):
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            conn.close()
            print("Successfully connected to the postgresql sm3 database")
            return True
        except psycopg2.OperationalError as e:
            print(f"Attempt {attempt + 1}/{max_retries} to connect to the postgresql sm3 database failed")
            print(f"Error: {e}")
            time.sleep(delay_seconds)

    raise Exception("Could not connect to the postgresql sm3 database after 60 maximum retries")

# Definition of the sm3 datatables
# ALERT: Hierarchy is important for the database to be built propery based on dependencies
def create_tables(conn):
    with conn.cursor() as cursor:
        create_table_commands = [
            """
                CREATE TABLE IF NOT EXISTS organizations (
                    Id UUID NOT NULL PRIMARY KEY,
                    NAME TEXT NOT NULL,
                    ADDRESS TEXT NOT NULL,
                    CITY VARCHAR(255) NOT NULL,
                    STATE TEXT NOT NULL,
                    ZIP TEXT NOT NULL,
                    LAT NUMERIC NOT NULL,
                    LON NUMERIC NOT NULL,
                    PHONE VARCHAR(255),
                    REVENUE NUMERIC NOT NULL,
                    UTILIZATION INTEGER NOT NULL
                    );
            """,
            """
                CREATE TABLE IF NOT EXISTS payers (
                    Id UUID NOT NULL PRIMARY KEY,
                    NAME TEXT NOT NULL,
                    OWNERSHIP VARCHAR(50) NOT NULL,
                    AMOUNT_COVERED NUMERIC NOT NULL,
                    AMOUNT_UNCOVERED NUMERIC NOT NULL,
                    REVENUE NUMERIC NOT NULL,
                    COVERED_ENCOUNTERS INTEGER NOT NULL,
                    UNCOVERED_ENCOUNTERS INTEGER NOT NULL,
                    COVERED_MEDICATIONS INTEGER NOT NULL,
                    UNCOVERED_MEDICATIONS INTEGER NOT NULL,
                    COVERED_PROCEDURES INTEGER NOT NULL,
                    UNCOVERED_PROCEDURES INTEGER NOT NULL,
                    COVERED_IMMUNIZATIONS INTEGER NOT NULL,
                    UNCOVERED_IMMUNIZATIONS INTEGER NOT NULL,
                    UNIQUE_CUSTOMERS INTEGER NOT NULL,
                    QOLS_AVG NUMERIC(10,6) NOT NULL,
                    MEMBER_MONTHS INTEGER NOT NULL, 
                    ADDRESS TEXT, 
                    CITY TEXT, 
                    ZIP INTEGER, 
                    state_headquartered TEXT, 
                    PHONE VARCHAR(255)
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS patients (
                    Id UUID NOT NULL PRIMARY KEY,
                    BIRTHDATE DATE NOT NULL,
                    DEATHDATE DATE,
                    SSN VARCHAR(11),
                    DRIVERS VARCHAR(255),
                    PASSPORT TEXT,
                    PREFIX VARCHAR(4),
                    FIRST VARCHAR(100) NOT NULL,
                    LAST VARCHAR(100) NOT NULL,
                    SUFFIX VARCHAR(10),
                    MAIDEN VARCHAR(100),
                    MARITAL CHAR(1),
                    RACE VARCHAR(50) NOT NULL,
                    ETHNICITY VARCHAR(50) NOT NULL,
                    GENDER CHAR(1) NOT NULL,
                    BIRTHPLACE TEXT NOT NULL,
                    ADDRESS TEXT NOT NULL,
                    CITY VARCHAR(100) NOT NULL,
                    STATE VARCHAR(100) NOT NULL,
                    COUNTY VARCHAR(100) NOT NULL,
                    FIPS NUMERIC,
                    ZIP VARCHAR(10),
                    LAT TEXT,
                    LON TEXT,
                    HEALTHCARE_EXPENSES NUMERIC NOT NULL,
                    HEALTHCARE_COVERAGE NUMERIC NOT NULL,
                    INCOME INTEGER NOT NULL
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS encounters (
                    Id UUID NOT NULL PRIMARY KEY,
                    START TIMESTAMP WITH TIME ZONE,
                    STOP TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    ORGANIZATION UUID REFERENCES organizations(Id),
                    PROVIDER UUID ,
                    PAYER UUID REFERENCES payers(Id),
                    ENCOUNTERCLASS TEXT,
                    CODE BIGINT,
                    DESCRIPTION TEXT,
                    BASE_ENCOUNTER_COST NUMERIC,
                    TOTAL_CLAIM_COST NUMERIC,
                    PAYER_COVERAGE NUMERIC,
                    REASONCODE BIGINT,
                    REASONDESCRIPTION TEXT
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS procedures (
                    START TIMESTAMP WITH TIME ZONE NOT NULL,
                    STOP TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    CODE BIGINT NOT NULL,
                    DESCRIPTION TEXT NOT NULL,
                    BASE_COST NUMERIC NOT NULL,
                    REASONCODE BIGINT,
                    REASONDESCRIPTION TEXT,
                    PRIMARY KEY (PATIENT, ENCOUNTER, CODE, START)
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS providers (
                    Id UUID NOT NULL PRIMARY KEY,
                    ORGANIZATION UUID NOT NULL,
                    NAME TEXT NOT NULL,
                    GENDER CHAR(1) NOT NULL,
                    SPECIALITY VARCHAR(255) NOT NULL,
                    ADDRESS TEXT NOT NULL,
                    CITY VARCHAR(100) NOT NULL,
                    STATE CHAR(2) NOT NULL,
                    ZIP VARCHAR(10) NOT NULL,
                    LAT NUMERIC(9,6) NOT NULL,
                    LON NUMERIC(9,6) NOT NULL,
                    ENCOUNTERS INTEGER NOT NULL,
                    PROCEDURES INTEGER NOT NULL
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS allergies (
                    START TIMESTAMP WITH TIME ZONE,
                    STOP TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    CODE BIGINT,
                    SYSTEM TEXT,
                    DESCRIPTION TEXT,
                    TYPE TEXT,
                    CATEGORY TEXT,
                    REACTION1 BIGINT,
                    DESCRIPTION1 TEXT,
                    SEVERITY1 TEXT,
                    REACTION2 BIGINT,
                    DESCRIPTION2 TEXT,
                    SEVERITY2 TEXT,
                    PRIMARY KEY (PATIENT, ENCOUNTER, CODE)
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS careplans (
                    Id UUID PRIMARY KEY,
                    START TIMESTAMP WITH TIME ZONE,
                    STOP TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    CODE BIGINT,
                    DESCRIPTION TEXT,
                    REASONCODE BIGINT,
                    REASONDESCRIPTION TEXT
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS claims (
                    Id UUID PRIMARY KEY,
                    PATIENTID UUID REFERENCES patients(Id),
                    PROVIDERID UUID REFERENCES providers(Id),
                    PRIMARYPATIENTINSURANCEID UUID,
                    SECONDARYPATIENTINSURANCEID UUID,
                    DEPARTMENTID BIGINT,
                    PATIENTDEPARTMENTID BIGINT,
                    DIAGNOSIS1 BIGINT,
                    DIAGNOSIS2 BIGINT,
                    DIAGNOSIS3 BIGINT,
                    DIAGNOSIS4 BIGINT,
                    DIAGNOSIS5 BIGINT,
                    DIAGNOSIS6 BIGINT,
                    DIAGNOSIS7 BIGINT,
                    DIAGNOSIS8 BIGINT,
                    REFERRINGPROVIDERID UUID REFERENCES providers(Id),
                    APPOINTMENTID UUID,
                    CURRENTILLNESSDATE TIMESTAMP WITH TIME ZONE,
                    SERVICEDATE TIMESTAMP WITH TIME ZONE,
                    SUPERVISINGPROVIDERID UUID REFERENCES providers(Id),
                    STATUS1 TEXT,
                    STATUS2 TEXT,
                    STATUSP TEXT,
                    OUTSTANDING1 TEXT,
                    OUTSTANDING2 TEXT,
                    OUTSTANDINGP TEXT,
                    LASTBILLEDDATE1 TIMESTAMP WITH TIME ZONE,
                    LASTBILLEDDATE2 TIMESTAMP WITH TIME ZONE,
                    LASTBILLEDDATEP TIMESTAMP WITH TIME ZONE,
                    HEALTHCARECLAIMTYPEID1 BIGINT,
                    HEALTHCARECLAIMTYPEID2 BIGINT
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS claims_transactions(
                    ID UUID PRIMARY KEY,
                    CLAIMID UUID REFERENCES claims(Id),
                    CHARGEID NUMERIC,
                    PATIENTID UUID REFERENCES patients(Id),
                    TYPE TEXT,
                    AMOUNT TEXT,
                    METHOD TEXT,
                    FROMDATE TIMESTAMP WITH TIME ZONE,
                    TODATE TIMESTAMP WITH TIME ZONE,
                    PLACEOFSERVICE TEXT,
                    PROCEDURECODE TEXT,
                    MODIFIER1 TEXT,
                    MODIFIER2 TEXT,
                    DIAGNOSISREF1 TEXT,
                    DIAGNOSISREF2 TEXT,
                    DIAGNOSISREF3 TEXT,
                    DIAGNOSISREF4 TEXT,
                    UNITS BIGINT,
                    DEPARTMENTID TEXT,
                    NOTES TEXT,
                    UNITAMOUNT TEXT,
                    TRANSFEROUTID TEXT,
                    TRANSFERTYPE TEXT,
                    PAYMENTS TEXT,
                    ADJUSTMENTS TEXT,
                    TRANSFERS TEXT,
                    OUTSTANDING TEXT,
                    APPOINTMENTID TEXT,
                    LINENOTE TEXT,
                    PATIENTINSURANCEID UUID,
                    FEESCHEDULEID TEXT,
                    PROVIDERID UUID REFERENCES providers(Id),
                    SUPERVISINGPROVIDERID UUID REFERENCES providers(Id)
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS conditions (
                    START TIMESTAMP WITH TIME ZONE,
                    STOP TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    CODE BIGINT,
                    DESCRIPTION TEXT,
                    PRIMARY KEY (PATIENT, ENCOUNTER, CODE)
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS devices (
                    START TIMESTAMP WITH TIME ZONE,
                    STOP TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    CODE BIGINT,
                    DESCRIPTION TEXT,
                    UDI TEXT,
                    PRIMARY KEY (PATIENT, ENCOUNTER, CODE, UDI)
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS imaging_studies (
                    Id UUID PRIMARY KEY,
                    DATE TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    SERIES_UID TEXT,
                    BODYSITE_CODE BIGINT,
                    BODYSITE_DESCRIPTION TEXT,
                    MODALITY_CODE TEXT,
                    MODALITY_DESCRIPTION TEXT,
                    INSTANCE_UID TEXT,
                    SOP_CODE TEXT,
                    SOP_DESCRIPTION TEXT,
                    PROCEDURE_CODE BIGINT
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS immunizations (
                    DATE TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    CODE BIGINT,
                    DESCRIPTION TEXT,
                    BASE_COST NUMERIC,
                    PRIMARY KEY (PATIENT, ENCOUNTER, CODE)
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS medications (
                    START TIMESTAMP WITH TIME ZONE NOT NULL,
                    STOP TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    PAYER UUID REFERENCES payers(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    CODE BIGINT NOT NULL,
                    DESCRIPTION TEXT NOT NULL,
                    BASE_COST NUMERIC NOT NULL,
                    PAYER_COVERAGE NUMERIC NOT NULL,
                    DISPENSES INTEGER NOT NULL,
                    TOTALCOST NUMERIC NOT NULL,
                    REASONCODE BIGINT,
                    REASONDESCRIPTION TEXT
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS observations (
                    DATE TIMESTAMP WITH TIME ZONE,
                    PATIENT UUID REFERENCES patients(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    CATEGORY TEXT,
                    CODE TEXT,
                    DESCRIPTION TEXT,
                    VALUE TEXT,
                    UNITS TEXT,
                    TYPE TEXT
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS payer_transitions (
                    PATIENT UUID REFERENCES patients(Id),
                    MEMBERID UUID,
                    START_DATE TIMESTAMP WITH TIME ZONE,
                    END_DATE TIMESTAMP WITH TIME ZONE,
                    PAYER UUID REFERENCES payers(Id),
                    SECONDARY_PAYER UUID REFERENCES payers(Id),
                    PLAN_OWNERSHIP VARCHAR ,
                    OWNER_NAME TEXT
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS supplies (
                    DATE TIMESTAMP WITH TIME ZONE NOT NULL,
                    PATIENT UUID REFERENCES patients(Id),
                    ENCOUNTER UUID REFERENCES encounters(Id),
                    CODE BIGINT NOT NULL,
                    DESCRIPTION TEXT NOT NULL,
                    QUANTITY INTEGER NOT NULL
                );
            """,
            """ 
                CREATE TABLE IF NOT EXISTS patient_expenses (
                    PATIENT_ID UUID REFERENCES patients(Id),
                    YEAR TIMESTAMP WITH TIME ZONE,
                    PAYER_ID UUID REFERENCES payers(Id),
                    HEALTHCARE_EXPENSES NUMERIC NOT NULL,
                    INSURANCE_COSTS NUMERIC NOT NULL,
                    COVERED_COSTS NUMERIC NOT NULL,
                    PRIMARY KEY (PATIENT_ID, YEAR, PAYER_ID)
                );
            """
        ]
        for command in create_table_commands:
            cursor.execute(command)
    conn.commit()

# Helper function extracting the explicit filename
def extract_filename(filepath: str):
    file_name_substrings = filepath.split('/')
    file_name_with_extention = file_name_substrings[-1]
    file_name = file_name_with_extention.split('.')[0]
    return file_name

# Function to load the synthea csv data directly into the database
def load_data(conn):
    #with conn.cursor() as cursor:
    # List of tables to load (in order of dependencies)
    tables = ["organizations", "payers", "patients", "encounters", "procedures", "providers", "allergies",
              "careplans", "claims",
              "claims_transactions", "conditions", "devices", "imaging_studies", "immunizations", "medications",
              "observations",
              "payer_transitions", "supplies", "patient_expenses"]
    cursor = conn.cursor()
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    #Session = sessionmaker(bind=engine)
    # Path to postgres datafile:
    data_path = "/data/"
    try:
        for table in tables:
            # TODO: checkpoint for the respective data already existing
            # IF true-> skip/ false -> execute addition
            csv_file = os.path.join(data_path, f"{table}.csv")
            sample_string = f"SELECT COUNT(*) from {table}"
            # calling of the sample query:
            cursor.execute(sample_string)
            # Fetch the respective values:
            table_exist = cursor.fetchone()[0]
            if not table_exist:
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    #change to lower case
                    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                    df.columns = [x.lower() for x in df.columns]
                    if table == 'payers':
                        df = df.loc[:, ~df.columns.str.contains('^Address')]
                        df = df.loc[:, ~df.columns.str.contains('^City')]
                        df = df.loc[:, ~df.columns.str.contains('^State_Headquatered')]
                        df = df.loc[:, ~df.columns.str.contains('^Zip')]
                        df = df.loc[:, ~df.columns.str.contains('^Phone')]
                    df_1 = df.drop_duplicates()
                    df = df_1
                    table_name = extract_filename(table)
                    # Checkpoint: Does data table already exist?
                    df.to_sql(table_name, con=engine, if_exists='append', index=False)
    except Exception as e:
        print('Error occured loading data into database')
    finally:
        cursor.close()

def main():
    # Backoff for connection to database container to be ready
    wait_for_db()
    # Database connection
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        # Create tables based on defined schema
        create_tables(conn)
        # Load synthea data
        load_data(conn)
        print("Database setup completed successfully")
    except Exception as e:
        print(f"Error during database setup: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()