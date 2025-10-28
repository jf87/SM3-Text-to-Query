# Imports of all the extentions
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
import os


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


def run_db_test(conn):
    with conn.cursor() as cursor:
        sql_test_query = [
            """
                SELECT DISTINCT p.first, p.last
                FROM organizations org
                LEFT JOIN encounters e ON org.id=e.organization LEFT JOIN patients p ON e.patient=p.id
                WHERE org.name='ROYAL OF FAIRHAVEN NURSING CENTER';
            """,
            """
            SELECT speciality 
            FROM providers pr 
            WHERE name = 'Crystle668 McCullough561';
            """,
            """
            SELECT bodysite_code, bodysite_description 
            FROM imaging_studies 
            WHERE id='ee88b224-1f91-8c6a-493a-46e8004c4331';""",
            """
            SELECT DISTINCT p.first, p.last 
            FROM immunizations im 
            LEFT JOIN patients p ON im.patient=p.id 
            WHERE im.description='Influenza  seasonal  injectable  preservative free';""",
            """
            SELECT description
            FROM devices
            WHERE code = '170615005';
            """,
            """
            SELECT DISTINCT code
            FROM supplies
            WHERE description = 'Continuous positive airway pressure nasal oxygen cannula (physical object)';
            """,
            """
            SELECT reasoncode, reasondescription 
            FROM encounters 
            WHERE id='79942d67-05c5-5c61-336d-4be332d76720';""",
            """
            SELECT DISTINCT p.first, p.last 
            FROM payers py 
            LEFT JOIN payer_transitions pt 
            ON py.id=pt.payer 
            LEFT JOIN patients p 
            ON pt.patient=p.id 
            WHERE py.id='0133f751-9229-3cfd-815f-b6d4979bdd6a';"""
        ]
        # Sidenote: add multiple connection test for all the different database tables
        for i, command in enumerate(sql_test_query, 1):
            print('\n')
            print(f'Test query: {i} \n')
            print('Queyr result:')
            cursor.execute(command)
            results = cursor.fetchall()
            for row in results:
                row_str = " | ".join([str(val) for val in row])
                print(row_str)
            print('\n')
    conn.commit()
# TODO sidenote Cedi: maybe extend such that: number of rows and format of columns is checked.
# TODO sidenote Cedi: define script, which can consume the experiment and compute the respective graphs. v2

def main():
    # Wait for connection to be available:
    wait_for_db()
    # Database connection:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        run_db_test(conn)
        print("PSQL database test is complete: check container log for results.")
    except Exception as e:
        print(f"Error during PSQL database check run: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()