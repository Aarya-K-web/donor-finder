import os
import mysql.connector
from mysql.connector import Error, pooling

# Database Connection Details
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'blood_organ_donor_db')

try:
    db_pool = pooling.MySQLConnectionPool(
        pool_name="donor_finder_pool",
        pool_size=5,
        pool_reset_session=True,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    print("Database Connection Pool successfully initialized.")
except Error as e:
    print(f"Warning: Failed to create database connection pool: {e}")
    db_pool = None

def get_db_connection():
    if db_pool:
        try:
            return db_pool.get_connection()
        except Error as e:
            print(f"Error acquiring connection from pool: {e}")
            raise e
    else:
        try:
            return mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
        except Error as e:
            print(f"Database connection error: {e}")
            raise e

def execute_query(query, params=None, fetch=False, commit=False):
    conn = None
    cursor = None
    result = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(query, params or ())
        
        if commit:
            conn.commit()
            result = cursor.lastrowid if cursor.lastrowid != 0 else cursor.rowcount
        elif fetch:
            result = cursor.fetchall()
            if result:
                for row in result:
                    for k, v in row.items():
                        if isinstance(v, set):
                            row[k] = ",".join(v)
            
    except Error as e:
        print(f"Database Query Error: {e}")
        if conn and commit:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

def call_procedure(proc_name, params=None):
    conn = None
    cursor = None
    results = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.callproc(proc_name, params or ())
        
        for result in cursor.stored_results():
            fetched = result.fetchall()
            if fetched:
                for row in fetched:
                    for k, v in row.items():
                        if isinstance(v, set):
                            row[k] = ",".join(v)
            results.extend(fetched)
            
    except Error as e:
        print(f"Database Stored Procedure Error: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return results
