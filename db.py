import os
import mysql.connector
from mysql.connector import Error, pooling

# Database Connection Details
# Reads from environment variables if present, otherwise falls back to defaults.
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'blood_organ_donor_db')

# Create a connection pool to manage connections efficiently
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
    print("The application will fallback to direct connections per request.")
    db_pool = None

def get_db_connection():
    """
    Acquires a database connection from the connection pool,
    or falls back to a direct connection if the pool is unavailable.
    """
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
    """
    Helper function to safely execute a SQL query.
    Handles connection acquisition, cursor creation, parameter binding,
    error logging, transaction commit/rollback, and resource cleanup.
    
    :param query: SQL string to execute.
    :param params: Tuple of parameters for SQL parameterization (prevents SQL injection).
    :param fetch: If True, fetches and returns all matching rows as dictionaries.
    :param commit: If True, commits the transaction (use for INSERT/UPDATE/DELETE).
    :return: List of dictionaries if fetch=True, inserted row ID or row count if commit=True.
    """
    conn = None
    cursor = None
    result = None
    try:
        conn = get_db_connection()
        # Using dictionary=True returns rows as Python dictionaries instead of tuples
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
    """
    Helper function to call a database stored procedure.
    Processes the returned result sets from the cursor.
    
    :param proc_name: Name of the stored procedure to call.
    :param params: Tuple of IN parameters for the procedure.
    :return: Combined list of dictionaries representing result sets from the procedure.
    """
    conn = None
    cursor = None
    results = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Execute the procedure
        cursor.callproc(proc_name, params or ())
        
        # mysql-connector-python stores procedure results in cursor.stored_results()
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
