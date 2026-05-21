from flask import Flask, render_template, request, redirect, url_for, flash
import db

app = Flask(__name__)
# Secret key is required for Flask session management and flash messages
app.secret_key = 'blood_organ_donor_finder_secret_key'

@app.route('/')
def index():
    """
    Home Route:
    Loads a dashboard showing real-time statistics fetched directly from the database.
    """
    stats = {}
    try:
        # Fetch total active available donors count from the 'available_donors' view
        donors_res = db.execute_query("SELECT COUNT(*) AS count FROM available_donors", fetch=True)
        stats['available_donors'] = donors_res[0]['count'] if donors_res else 0
        
        # Fetch pending blood requests count
        blood_res = db.execute_query("SELECT COUNT(*) AS count FROM blood_requests WHERE status = 'Pending'", fetch=True)
        stats['pending_blood'] = blood_res[0]['count'] if blood_res else 0
        
        # Fetch pending organ requests count
        organ_res = db.execute_query("SELECT COUNT(*) AS count FROM organ_requests WHERE status = 'Pending'", fetch=True)
        stats['pending_organ'] = organ_res[0]['count'] if organ_res else 0
        
    except Exception as e:
        print(f"Error fetching stats for index: {e}")
        # Default to zeroes if the database hasn't been created or is unreachable
        stats = {'available_donors': 0, 'pending_blood': 0, 'pending_organ': 0}
        flash("Could not connect to database. Make sure schema.sql has been imported and MySQL is running.", "danger")
        
    return render_template('index.html', stats=stats)

@app.route('/donors')
def view_donors():
    """
    Available Donors Route:
    Retrieves and displays all active donors from the 'available_donors' view.
    """
    try:
        donors = db.execute_query("SELECT * FROM available_donors", fetch=True)
    except Exception as e:
        print(f"Error viewing donors: {e}")
        donors = []
        flash("Error loading available donors view. Check your database connection.", "danger")
    
    return render_template('donors.html', donors=donors)

@app.route('/search', methods=['GET', 'POST'])
def search_donors():
    """
    Search Route:
    Handles searching for available donors using a blood type and optional city.
    Queries the available_donors view directly.
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
                # Query the available_donors view directly, aliasing blood_type as donor_blood_type for template compatibility
                query = "SELECT *, blood_type AS donor_blood_type FROM available_donors WHERE blood_type = %s"
                params = [blood_type]
                if city:
                    query += " AND LOWER(city) = LOWER(%s)"
                    params.append(city)
                results = db.execute_query(query, params, fetch=True)
            except Exception as e:
                print(f"Error querying available donors view: {e}")
                flash(f"Error executing search: {e}", "danger")
                
    return render_template('search.html', results=results, searched=searched, blood_type=blood_type, city=city)

if __name__ == '__main__':
    app.run()
