from flask import Flask, render_template, request, redirect, url_for, flash, session
import db

app = Flask(__name__)
# Secret key is required for Flask session management and flash messages
app.secret_key = 'blood_organ_donor_finder_secret_key'

@app.route('/')
def index():
    """
    Landing Page Route:
    Greets visitors with a premium dashboard introducing the Lifeline Link portal, 
    key database design specifications, and direct action prompts.
    """
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """
    Dashboard Route:
    Displays database metrics (active counts), the tabular view of available donors, 
    and recent blood & organ request queues inside an administrative overview panel.
    """
    # Protect dashboard: only logged-in users can access it
    if 'user_id' not in session:
        flash("Please login to access the dashboard.", "warning")
        return redirect(url_for('login'))

    stats = {}
    donors = []
    blood_requests = []
    organ_requests = []
    
    try:
        # Fetch general stats from available donors view and request tables
        donors_res = db.execute_query("SELECT COUNT(*) AS count FROM available_donors", fetch=True)
        stats['available_donors'] = donors_res[0]['count'] if donors_res else 0
        
        blood_res = db.execute_query("SELECT COUNT(*) AS count FROM blood_requests WHERE status = 'Pending'", fetch=True)
        stats['pending_blood'] = blood_res[0]['count'] if blood_res else 0
        
        organ_res = db.execute_query("SELECT COUNT(*) AS count FROM organ_requests WHERE status = 'Pending'", fetch=True)
        stats['pending_organ'] = organ_res[0]['count'] if organ_res else 0
        
        # Fetch the entire table view for available donors
        donors = db.execute_query("SELECT * FROM available_donors", fetch=True)
        
        # Fetch top 5 recent blood and organ requests (joined with user table to resolve name)
        blood_requests = db.execute_query(
            "SELECT br.*, u.name AS recipient_name FROM blood_requests br JOIN users u ON br.recipient_id = u.user_id ORDER BY br.request_date DESC LIMIT 5",
            fetch=True
        )
        organ_requests = db.execute_query(
            "SELECT orq.*, u.name AS recipient_name FROM organ_requests orq JOIN users u ON orq.recipient_id = u.user_id ORDER BY orq.request_date DESC LIMIT 5",
            fetch=True
        )
        
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        stats = {'available_donors': 0, 'pending_blood': 0, 'pending_organ': 0}
        flash("Could not connect to database. Make sure schema.sql has been imported and MySQL is running.", "danger")
        
    return render_template('dashboard.html', stats=stats, donors=donors, blood_requests=blood_requests, organ_requests=organ_requests)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration Route:
    Saves a new user record. If the selected type is a 'Donor', it transactionalizes
    the creation of the matching profile (blood type, willing organs, location)
    in the database, validating all constraints.
    Automatically logs in the user on success.
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        if not name or not email or not phone or not password or not user_type:
            flash("All profile fields are required.", "warning")
            return render_template('register.html')
            
        try:
            # 1. Insert into base users table (commits record and returns the new AUTO_INCREMENT user_id)
            user_id = db.execute_query(
                "INSERT INTO users (name, email, phone, password_hash, user_type) VALUES (%s, %s, %s, %s, %s)",
                (name, email, phone, password, user_type),
                commit=True
            )
            
            # 2. If role is 'Donor', populate secondary 'donors' table profile details
            if user_type == 'Donor':
                blood_type = request.form.get('blood_type')
                city = request.form.get('city')
                organs_list = request.form.getlist('organs')
                organs_willing = ",".join(organs_list) if organs_list else None
                
                if not blood_type or not city:
                    # Enforce rollback manually in our user-flow due to input omission
                    db.execute_query("DELETE FROM users WHERE user_id = %s", (user_id,), commit=True)
                    flash("Donor profile details (Blood Type, City) are required for active donors.", "warning")
                    return render_template('register.html')
                
                db.execute_query(
                    "INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status) VALUES (%s, %s, %s, %s, 'Available')",
                    (user_id, blood_type, organs_willing, city),
                    commit=True
                )
            
            # Auto-login the user on successful registration
            session['user_id'] = user_id
            session['name'] = name
            session['user_type'] = user_type
            
            flash(f"Account successfully created for {name}! You are now logged in.", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Error during registration insert: {e}")
            flash(f"Registration failed: {e}. Check if email is already registered.", "danger")
            
    return render_template('register.html')

@app.route('/register-donor', methods=['GET', 'POST'])
def register_donor():
    """
    Donor Registration Route:
    Allows an already registered, logged-in user to upgrade/set up a donor profile.
    Inserts into the 'donors' table and synchronizes their user type.
    """
    if 'user_id' not in session:
        flash("Please login to register as a donor.", "warning")
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    
    # Check if the user already has an active donor profile
    try:
        existing = db.execute_query("SELECT * FROM donors WHERE user_id = %s", (user_id,), fetch=True)
        if existing:
            flash("You are already registered as a donor!", "info")
            return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Error checking existing donor profile: {e}")
        
    if request.method == 'POST':
        blood_type = request.form.get('blood_type')
        city = request.form.get('city')
        organs_list = request.form.getlist('organs')
        organs_willing = ",".join(organs_list) if organs_list else None
        availability = request.form.get('availability')
        
        status = 'Available' if availability == 'Yes' else 'Unavailable'
        
        if not blood_type or not city:
            flash("Blood Type and City are required fields.", "warning")
            return render_template('register_donor.html')
            
        try:
            # 1. Insert into donors table
            db.execute_query(
                "INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status) VALUES (%s, %s, %s, %s, %s)",
                (user_id, blood_type, organs_willing, city, status),
                commit=True
            )
            
            # 2. Update user_type in users table to 'Donor'
            db.execute_query(
                "UPDATE users SET user_type = 'Donor' WHERE user_id = %s",
                (user_id,),
                commit=True
            )
            
            # 3. Update session user_type
            session['user_type'] = 'Donor'
            
            flash("Thank you! Your donor profile has been successfully registered and activated.", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Error registering donor: {e}")
            flash(f"Failed to register donor: {e}", "danger")
            
    return render_template('register_donor.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login Route:
    Handles checking user credentials. Compares plain text passwords as requested.
    Establishes an active user session on success.
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash("Please fill in all credentials.", "warning")
            return render_template('login.html')
            
        try:
            # Query matching email and password (storing password as plain text in password_hash column)
            users = db.execute_query(
                "SELECT * FROM users WHERE email = %s AND password_hash = %s",
                (email, password),
                fetch=True
            )
            
            if users:
                user = users[0]
                session['user_id'] = user['user_id']
                session['name'] = user['name']
                session['user_type'] = user['user_type']
                
                flash(f"Welcome back, {user['name']}!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password. Please try again.", "danger")
        except Exception as e:
            print(f"Error during login authentication: {e}")
            flash("Database authentication failed. Please verify schema.sql is active.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Logout Route:
    Clears all active session keys to safely log out the current user.
    """
    session.clear()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('index'))

@app.route('/request', methods=['GET', 'POST'])
def make_request():
    """
    Request Posting Route:
    Allows user accounts acting as Recipients/Admins to submit new urgent emergencies,
    routing details to either the 'blood_requests' or 'organ_requests' tables based on inputs.
    """
    # Protect request: only logged-in users can post requests
    if 'user_id' not in session:
        flash("Please login to submit requests.", "warning")
        return redirect(url_for('login'))

    recipients = []
    try:
        # Fetch users acting as Recipient or Admin to display as the requesting entity
        recipients = db.execute_query("SELECT user_id, name FROM users WHERE user_type IN ('Recipient', 'Admin')", fetch=True)
    except Exception as e:
        print(f"Error fetching request candidates: {e}")
        
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        request_type = request.form.get('request_type') # 'Blood' or 'Organ'
        city = request.form.get('city')
        hospital = request.form.get('hospital_name')
        urgency = request.form.get('urgency_level')
        
        if not recipient_id or not request_type or not city or not hospital or not urgency:
            flash("Please complete all standard fields.", "warning")
            return render_template('request.html', recipients=recipients)
            
        try:
            if request_type == 'Blood':
                blood_type = request.form.get('blood_type')
                quantity = request.form.get('quantity_ml')
                if not blood_type or not quantity:
                    flash("Blood type and quantity in ml are required.", "warning")
                    return render_template('request.html', recipients=recipients)
                
                db.execute_query(
                    "INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')",
                    (recipient_id, blood_type, quantity, hospital, city, urgency),
                    commit=True
                )
            else:
                organ_type = request.form.get('organ_type')
                if not organ_type:
                    flash("Organ type is required for transplants.", "warning")
                    return render_template('request.html', recipients=recipients)
                
                db.execute_query(
                    "INSERT INTO organ_requests (recipient_id, organ_type, hospital_name, city, urgency_level, status) VALUES (%s, %s, %s, %s, %s, 'Pending')",
                    (recipient_id, organ_type, hospital, city, urgency),
                    commit=True
                )
                
            flash("Your request has been successfully submitted and matched with the database queue.", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Error submitting request: {e}")
            flash(f"Failed to post request: {e}", "danger")
            
    return render_template('request.html', recipients=recipients)

@app.route('/search', methods=['GET', 'POST'])
def search_donors():
    """
    Search Route:
    Searches available donors by blood type and city directly from the available_donors view.
    """
    results = []
    searched = False
    blood_type = ""
    city = ""
    
    if request.method == 'POST':
        blood_type = request.form.get('blood_type')
        city = request.form.get('city', '').strip()
        searched = True
        
        if not blood_type:
            flash("Please specify a blood type to search.", "warning")
        else:
            try:
                # Query the available_donors view directly by blood type and optionally city
                query = "SELECT * FROM available_donors WHERE blood_type = %s"
                params = [blood_type]
                if city:
                    query += " AND LOWER(city) = LOWER(%s)"
                    params.append(city)
                results = db.execute_query(query, params, fetch=True)
            except Exception as e:
                print(f"Error querying available donors view: {e}")
                flash(f"Error executing search: {e}", "danger")
                
    return render_template('search.html', results=results, searched=searched, blood_type=blood_type, city=city)

@app.route('/match/<req_type>/<int:req_id>')
def match_request(req_type, req_id):
    """
    Match Request Route:
    Resolves the emergency request, matches it against available compatible donors in the same city,
    and displays the results.
    """
    if 'user_id' not in session:
        flash("Please login to perform matching operations.", "warning")
        return redirect(url_for('login'))

    request_info = None
    donors = []
    try:
        # 1. Fetch details of the request based on type
        if req_type == 'Blood':
            query = """
                SELECT br.*, u.name AS recipient_name, u.email AS recipient_email, u.phone AS recipient_phone 
                FROM blood_requests br 
                JOIN users u ON br.recipient_id = u.user_id 
                WHERE br.request_id = %s
            """
            rows = db.execute_query(query, (req_id,), fetch=True)
            if rows:
                request_info = rows[0]
                # Call stored procedure FindCompatibleDonors with recipient blood type and city
                proc_results = db.call_procedure('FindCompatibleDonors', (request_info['blood_type'], request_info['city']))
                
                # Standardize columns: map 'donor_blood_type' back to 'blood_type' for template uniformity
                donors = []
                for d in proc_results:
                    d_copy = dict(d)
                    d_copy['blood_type'] = d.get('donor_blood_type') or d.get('blood_type')
                    donors.append(d_copy)
        
        elif req_type == 'Organ':
            query = """
                SELECT orq.*, u.name AS recipient_name, u.email AS recipient_email, u.phone AS recipient_phone 
                FROM organ_requests orq 
                JOIN users u ON orq.recipient_id = u.user_id 
                WHERE orq.request_id = %s
            """
            rows = db.execute_query(query, (req_id,), fetch=True)
            if rows:
                request_info = rows[0]
                # Find available donors willing to donate this specific organ in the same city
                organ_query = """
                    SELECT * FROM available_donors 
                    WHERE FIND_IN_SET(%s, organs_willing_to_donate) > 0
                      AND LOWER(city) = LOWER(%s)
                """
                donors = db.execute_query(organ_query, (request_info['organ_type'], request_info['city']), fetch=True)
        
        if not request_info:
            flash("Request not found.", "danger")
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        print(f"Error matching request: {e}")
        flash(f"Error fetching compatibility matches: {e}", "danger")
        return redirect(url_for('dashboard'))

    return render_template('match_options.html', req_type=req_type, request_info=request_info, donors=donors)

@app.route('/match/confirm', methods=['POST'])
def confirm_match():
    """
    Confirm Match Route:
    Creates a new entry in the matches table, updates the request status to 'Matched',
    and displays the donor's contact card.
    """
    if 'user_id' not in session:
        flash("Please login to confirm match.", "warning")
        return redirect(url_for('login'))

    donor_id = request.form.get('donor_id')
    req_type = request.form.get('req_type')
    req_id = request.form.get('req_id')

    if not donor_id or not req_type or not req_id:
        flash("Missing parameters for match confirmation.", "warning")
        return redirect(url_for('dashboard'))

    try:
        # 1. Fetch matching donor contact info from available_donors view
        donor_res = db.execute_query("SELECT * FROM available_donors WHERE donor_id = %s", (donor_id,), fetch=True)
        if not donor_res:
            flash("Donor profile is no longer available.", "danger")
            return redirect(url_for('dashboard'))
        donor_info = donor_res[0]

        # 2. Check and branch inserts for matches table
        if req_type == 'Blood':
            # Create a match for blood request
            db.execute_query(
                "INSERT INTO matches (donor_id, blood_request_id, match_type, status) VALUES (%s, %s, 'Blood', 'Pending')",
                (donor_id, req_id),
                commit=True
            )
            # Update blood request status to 'Matched'
            db.execute_query(
                "UPDATE blood_requests SET status = 'Matched' WHERE request_id = %s",
                (req_id,),
                commit=True
            )
            # Fetch request details to show on success screen
            req_query = "SELECT hospital_name, city, blood_type AS target FROM blood_requests WHERE request_id = %s"
            req_res = db.execute_query(req_query, (req_id,), fetch=True)
            request_details = req_res[0] if req_res else None

        elif req_type == 'Organ':
            # Create a match for organ request
            db.execute_query(
                "INSERT INTO matches (donor_id, organ_request_id, match_type, status) VALUES (%s, %s, 'Organ', 'Pending')",
                (donor_id, req_id),
                commit=True
            )
            # Update organ request status to 'Matched'
            db.execute_query(
                "UPDATE organ_requests SET status = 'Matched' WHERE request_id = %s",
                (req_id,),
                commit=True
            )
            # Fetch request details to show on success screen
            req_query = "SELECT hospital_name, city, organ_type AS target FROM organ_requests WHERE request_id = %s"
            req_res = db.execute_query(req_query, (req_id,), fetch=True)
            request_details = req_res[0] if req_res else None

        else:
            flash("Invalid match category.", "danger")
            return redirect(url_for('dashboard'))

        flash(f"Database match successfully created! The new match is recorded and logged.", "success")
        return render_template('match_success.html', donor=donor_info, req_type=req_type, request_details=request_details)

    except Exception as e:
        print(f"Error during match confirmation: {e}")
        flash(f"Failed to record match: {e}", "danger")
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run()
