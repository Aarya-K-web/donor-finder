import os
import sys
import mysql.connector

def run():
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_name = os.environ.get('DB_NAME', 'blood_organ_donor_db')

    print(f"[1/3] Connecting to MySQL on {db_host}...")
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password)
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)
        
    cursor = conn.cursor()
    print(f"[2/3] Clearing and recreating database '{db_name}'...")
    cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
    cursor.execute(f"CREATE DATABASE {db_name}")
    cursor.execute(f"USE {db_name}")
    cursor.close()
    
    # Helper to execute SQL file with custom delimiter parsing
    def execute_sql_file(filename):
        print(f" -> Processing '{filename}'...")
        statement = ""
        delimiter = ";"
        cursor = conn.cursor()
        
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                # Skip comments and empty lines
                if not stripped or stripped.startswith("--"):
                    continue
                # Resolve DELIMITER statement changes (standard in triggers/procedures)
                if stripped.lower().startswith("delimiter"):
                    delimiter = stripped.split()[1]
                    continue
                
                statement += line + "\n"
                if stripped.endswith(delimiter):
                    exec_stmt = statement.strip()
                    if exec_stmt.endswith(delimiter):
                        exec_stmt = exec_stmt[:-len(delimiter)].strip()
                    if exec_stmt:
                        try:
                            cursor.execute(exec_stmt)
                        except Exception as ex:
                            print(f"[ERROR] Query Execution Failed:\n{exec_stmt}\nReason: {ex}")
                            cursor.close()
                            raise ex
                    statement = ""
        cursor.close()

    try:
        execute_sql_file("schema.sql")
        conn.commit()
        print(" -> Schema structures imported successfully!")
        
        execute_sql_file("sample_inserts.sql")
        conn.commit()
        print(" -> 15 realistic donors & 5 requests loaded successfully!")
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        conn.close()
        sys.exit(1)
        
    conn.close()
    print("[3/3] Database initialization completed successfully!")

if __name__ == '__main__':
    run()
