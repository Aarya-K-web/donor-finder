import os
import sys
import unittest
import mysql.connector

# Append local path so that db and app modules can be loaded properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Ensure we are pointing to the test database
os.environ['DB_NAME'] = 'blood_organ_donor_test_db'
os.environ['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', '060712')

def setup_test_database():
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '060712')
    db_name = os.environ.get('DB_NAME', 'blood_organ_donor_test_db')

    print(f"Connecting to MySQL on {db_host} to setup test database...")
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password)
    except Exception as e:
        print(f"[ERROR] Failed to connect to MySQL to setup test database: {e}")
        print("Please check that MySQL is running and password matches.")
        sys.exit(1)
        
    cursor = conn.cursor()
    print(f"Dropping and recreating database '{db_name}'...")
    cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
    cursor.execute(f"CREATE DATABASE {db_name}")
    cursor.execute(f"USE {db_name}")
    cursor.close()

    # Read and run schema.sql & sample_inserts.sql
    def execute_sql_file(filename):
        print(f" -> Executing SQL file: '{filename}'...")
        statement = ""
        delimiter = ";"
        cursor = conn.cursor()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(base_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.replace('blood_organ_donor_db', 'blood_organ_donor_test_db')
                stripped = line.strip()
                if not stripped or stripped.startswith("--"):
                    continue
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
                            print(f"[ERROR] Execution failed for statement:\n{exec_stmt}\nReason: {ex}")
                            cursor.close()
                            raise ex
                    statement = ""
        cursor.close()

    try:
        execute_sql_file("schema.sql")
        conn.commit()
        execute_sql_file("sample_inserts.sql")
        conn.commit()
        print("Database schema and sample rows initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to populate schema/inserts: {e}")
        conn.close()
        sys.exit(1)
        
    conn.close()

# Execute test database creation
setup_test_database()

# Now safe to import db and app since environment and database are ready
import db
import app

class LifelineLinkTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        self.app = app.app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.secret_key = 'test_secret_key'
        self.client = self.app.test_client()
        
    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        # Drop the test database after all tests are finished
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', '060712')
        db_name = os.environ.get('DB_NAME', 'blood_organ_donor_test_db')
        
        print("\nCleaning up test environment...")
        
        # Close connection pool first if possible
        if db.db_pool:
            try:
                # Close pooled connections
                pass
            except Exception:
                pass

        try:
            conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password)
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
            cursor.close()
            conn.close()
            print("Test database dropped successfully.")
        except Exception as e:
            print(f"Warning: Failed to drop test database: {e}")

    # =========================================================================
    # SECTION 1: DATABASE MODULE TESTS (db.py)
    # =========================================================================
    
    def test_db_connection_and_queries(self):
        """Test database connection, select query execution, and dictionary formatting."""
        # Query total users in test setup
        res = db.execute_query("SELECT COUNT(*) AS count FROM users", fetch=True)
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 1)
        self.assertGreater(res[0]['count'], 0)

        # Test SELECT on available_donors view
        donors = db.execute_query("SELECT * FROM available_donors", fetch=True)
        self.assertIsNotNone(donors)
        self.assertGreater(len(donors), 0)
        # Verify columns exist
        self.assertIn('donor_name', donors[0])
        self.assertIn('blood_type', donors[0])
        self.assertIn('city', donors[0])

    def test_db_stored_procedure(self):
        """Test executing FindCompatibleDonors stored procedure."""
        # Find compatible donors for O+ in Mumbai (should match O- John Doe)
        res = db.call_procedure('FindCompatibleDonors', ('O+', 'Mumbai'))
        self.assertIsNotNone(res)
        self.assertGreater(len(res), 0)
        
        # Search for John Doe in matches
        john_found = False
        for donor in res:
            if donor['donor_name'] == 'John Doe':
                john_found = True
                self.assertEqual(donor['donor_blood_type'], 'O-')
                self.assertEqual(donor['city'], 'Mumbai')
        self.assertTrue(john_found, "John Doe (O-) not found as a compatible donor for O+ in Mumbai")

    # =========================================================================
    # SECTION 2: FLASK ROUTE & INTERACTION TESTS
    # =========================================================================

    def test_index_route(self):
        """Test that index/landing page renders successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check standard brand headers and keywords
        self.assertIn(b'LifeLine Link', response.data)
        self.assertIn(b'Saving Lives', response.data)

    def test_dashboard_authentication_protection(self):
        """Test that dashboard route requires active user login."""
        # Without session, should redirect to login
        response = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_login_and_logout_flow(self):
        """Test login authentication and logout flow."""
        # 1. Test failed login
        response = self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'incorrect_password'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)

        # 2. Test successful login
        response = self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'hashed_pass_1' # standard plain password in sample inserts
        }, follow_redirects=True)
        self.assertIn(b'Welcome back, John Doe!', response.data)
        self.assertIn(b'Administrative Dashboard', response.data)

        # 3. Test logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'You have been successfully logged out', response.data)

    def test_registration_workflow(self):
        """Test recipient and donor registrations, including validations."""
        # 1. Test recipient registration
        response = self.client.post('/register', data={
            'name': 'Sarah Parker',
            'email': 'sarah.p@example.com',
            'phone': '9898989898',
            'password': 'sarahpass123',
            'user_type': 'Recipient'
        }, follow_redirects=True)
        self.assertIn(b'Account successfully created for Sarah Parker!', response.data)
        
        # Log out Sarah Parker so next registration request isn't redirected to dashboard
        self.client.get('/logout', follow_redirects=True)
        
        # 2. Test donor registration with missing donor-specific requirements
        response = self.client.post('/register', data={
            'name': 'Michael Jordan',
            'email': 'mj.test@example.com',
            'phone': '9111111111',
            'password': 'password23',
            'user_type': 'Donor',
            'blood_type': '',  # missing blood type
            'city': 'Chicago'
        }, follow_redirects=True)
        self.assertIn(b'Donor profile details (Blood Type, City) are required', response.data)

        # 3. Test donor registration with valid details
        response = self.client.post('/register', data={
            'name': 'David Beckham',
            'email': 'david.b@example.com',
            'phone': '9222222222',
            'password': 'password456',
            'user_type': 'Donor',
            'blood_type': 'A-',
            'city': 'Mumbai',
            'organs': ['Kidney', 'Cornea']
        }, follow_redirects=True)
        self.assertIn(b'Account successfully created for David Beckham!', response.data)

        # Confirm user is active in DB as a Donor
        user_res = db.execute_query("SELECT * FROM users WHERE email = 'david.b@example.com'", fetch=True)
        self.assertEqual(len(user_res), 1)
        self.assertEqual(user_res[0]['user_type'], 'Donor')
        
        donor_res = db.execute_query("SELECT * FROM donors WHERE user_id = %s", (user_res[0]['user_id'],), fetch=True)
        self.assertEqual(len(donor_res), 1)
        self.assertEqual(donor_res[0]['blood_type'], 'A-')
        self.assertEqual(donor_res[0]['city'], 'Mumbai')
        self.assertEqual(set(donor_res[0]['organs_willing_to_donate'].split(',')), {'Kidney', 'Cornea'})

    def test_donor_profile_upgrade(self):
        """Test upgrading a standard Recipient account to a Donor profile."""
        # First login as Alice Brown (Recipient in default inserts)
        with self.client.session_transaction() as sess:
            sess['user_id'] = 4
            sess['name'] = 'Alice Brown'
            sess['user_type'] = 'Recipient'

        # Upgrade account to Donor
        response = self.client.post('/register-donor', data={
            'blood_type': 'B-',
            'city': 'Pune',
            'organs': ['Liver', 'Lung'],
            'availability': 'Yes'
        }, follow_redirects=True)
        self.assertIn(b'donor profile has been successfully registered and activated', response.data)

        # Confirm details in DB
        user_res = db.execute_query("SELECT user_type FROM users WHERE user_id = 4", fetch=True)
        self.assertEqual(user_res[0]['user_type'], 'Donor')
        
        donor_res = db.execute_query("SELECT * FROM donors WHERE user_id = 4", fetch=True)
        self.assertEqual(len(donor_res), 1)
        self.assertEqual(donor_res[0]['blood_type'], 'B-')
        self.assertEqual(donor_res[0]['city'], 'Pune')
        self.assertEqual(donor_res[0]['availability_status'], 'Available')

    def test_blood_and_organ_request_posting(self):
        """Test submitting emergency requests for both blood and organs."""
        # Login as Admin User (can act as recipient/admin)
        with self.client.session_transaction() as sess:
            sess['user_id'] = 8
            sess['name'] = 'Admin User'
            sess['user_type'] = 'Admin'

        # 1. Submit Blood Request
        response = self.client.post('/request', data={
            'recipient_id': '8',
            'request_type': 'Blood',
            'city': 'Mumbai',
            'hospital_name': 'Hiranandani Hospital',
            'urgency_level': 'Critical',
            'blood_type': 'A-',
            'quantity_ml': '300'
        }, follow_redirects=True)
        self.assertIn(b'Your request has been successfully submitted', response.data)

        # Verify Blood Request was logged in database
        blood_res = db.execute_query("SELECT * FROM blood_requests WHERE recipient_id = 8 ORDER BY request_date DESC LIMIT 1", fetch=True)
        self.assertEqual(len(blood_res), 1)
        self.assertEqual(blood_res[0]['blood_type'], 'A-')
        self.assertEqual(blood_res[0]['quantity_ml'], 300)
        self.assertEqual(blood_res[0]['urgency_level'], 'Critical')
        self.assertEqual(blood_res[0]['status'], 'Pending')

        # 2. Submit Organ Request
        response = self.client.post('/request', data={
            'recipient_id': '8',
            'request_type': 'Organ',
            'city': 'Delhi',
            'hospital_name': 'Apollo Hospital',
            'urgency_level': 'Urgent',
            'organ_type': 'Lung'
        }, follow_redirects=True)
        self.assertIn(b'Your request has been successfully submitted', response.data)

        # Verify Organ Request was logged in database
        organ_res = db.execute_query("SELECT * FROM organ_requests WHERE recipient_id = 8 ORDER BY request_date DESC LIMIT 1", fetch=True)
        self.assertEqual(len(organ_res), 1)
        self.assertEqual(organ_res[0]['organ_type'], 'Lung')
        self.assertEqual(organ_res[0]['urgency_level'], 'Urgent')
        self.assertEqual(organ_res[0]['status'], 'Pending')

    def test_search_donors_endpoint(self):
        """Test searching available donors view by blood type and city."""
        # Search B+ in Mumbai (Jane Smith is B+, but Mumbai has John Doe O- and Charlie/Robert/etc)
        # O- is compatible with everything, but search_donors filters by exact blood_type in view.
        # Let's search O- in Mumbai
        response = self.client.post('/search', data={
            'blood_type': 'O-',
            'city': 'Mumbai'
        })
        self.assertEqual(response.status_code, 200)
        # Should display John Doe (O- in Mumbai)
        self.assertIn(b'John Doe', response.data)
        self.assertIn(b'O-', response.data)

    def test_match_options_generation(self):
        """Test fetching the /match options page using compatible donor stored procedures."""
        # Create a fresh blood request for A+ in Delhi
        req_id = db.execute_query(
            "INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')",
            (4, 'A+', 450, 'Max Hospital', 'Delhi', 'Normal'),
            commit=True
        )

        with self.client.session_transaction() as sess:
            sess['user_id'] = 8
            sess['name'] = 'Admin User'
            sess['user_type'] = 'Admin'

        # Fetch match options (calls FindCompatibleDonors procedure)
        response = self.client.get(f'/match/Blood/{req_id}')
        self.assertEqual(response.status_code, 200)
        # Jane Smith is A+ in Delhi, so she should be offered as a match
        self.assertIn(b'Jane Smith', response.data)

    def test_match_confirmation_and_triggers(self):
        """Test confirming a match, checking status updates, and trigger-created audit logs."""
        # Insert a pending blood request
        req_id = db.execute_query(
            "INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')",
            (4, 'O-', 300, 'Kokilaben Hospital', 'Mumbai', 'Critical'),
            commit=True
        )

        # Login
        with self.client.session_transaction() as sess:
            sess['user_id'] = 8
            sess['name'] = 'Admin User'
            sess['user_type'] = 'Admin'

        # John Doe is Donor ID 1 (O- in Mumbai)
        response = self.client.post('/match/confirm', data={
            'donor_id': '1',
            'req_type': 'Blood',
            'req_id': str(req_id)
        }, follow_redirects=True)
        
        self.assertIn(b'Database match successfully created', response.data)
        self.assertIn(b'John Doe', response.data)
        self.assertIn(b'john.doe@example.com', response.data) # Contact details revealed

        # 1. Verify blood_request status updated to 'Matched'
        req_res = db.execute_query("SELECT status FROM blood_requests WHERE request_id = %s", (req_id,), fetch=True)
        self.assertEqual(req_res[0]['status'], 'Matched')

        # 2. Verify match row was created in matches table
        match_res = db.execute_query("SELECT * FROM matches WHERE blood_request_id = %s", (req_id,), fetch=True)
        self.assertEqual(len(match_res), 1)
        self.assertEqual(match_res[0]['donor_id'], 1)
        self.assertEqual(match_res[0]['match_type'], 'Blood')
        self.assertEqual(match_res[0]['status'], 'Pending')

        # 3. Verify MySQL Trigger 'after_match_insert' successfully logged action in audit_log
        audit_res = db.execute_query("SELECT * FROM audit_log WHERE match_id = %s", (match_res[0]['match_id'],), fetch=True)
        self.assertEqual(len(audit_res), 1)
        self.assertEqual(audit_res[0]['action_type'], 'CREATE_MATCH')
        self.assertEqual(audit_res[0]['donor_id'], 1)
        self.assertEqual(audit_res[0]['request_id'], req_id)
        self.assertEqual(audit_res[0]['match_type'], 'Blood')
        self.assertIn('A new blood match was created', audit_res[0]['details'])

if __name__ == '__main__':
    unittest.main()
