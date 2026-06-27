from flask import Flask, render_template, request, redirect, url_for, flash, session
import uuid
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Admin credentials (in production, use a database)
__ADMIN_USERNAME = __'admin'
__ADMIN_PASSWORD= __'admin123'

# In-memory databases
users = {}  # {username: {password, name, email, created_at}}
leave_records = []  # Each record: {id, username, name, from_date, to_date, reason, status}

# ------------------- Decorators for Authentication -------------------

def login_required(f):
    """Decorator to protect routes that require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_logged_in'):
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login to access the admin panel.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------- User Authentication Routes -------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if session.get('user_logged_in'):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validation
        if not all([username, password, confirm_password, full_name, email]):
            flash('All fields are required!', 'warning')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
        
        if username in users:
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html')
        
        # Create new user
        users[username] = {
            'password': password,  # In production, hash this!
            'name': full_name,
            'email': email,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if session.get('user_logged_in'):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('login.html')
        
        if username in users and users[username]['password'] == password:
            session['user_logged_in'] = True
            session['username'] = username
            session['user_name'] = users[username]['name']
            flash(f'Welcome back, {users[username]["name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.pop('user_logged_in', None)
    session.pop('username', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ------------------- Leave Application Routes -------------------

@app.route('/')
@login_required
def index():
    """Home page - Leave application form (protected)"""
    return render_template('apply.html', user_name=session.get('user_name'))

@app.route('/apply', methods=['POST'])
@login_required
def apply_leave():
    """Process leave application"""
    username = session.get('username')
    name = request.form.get('name', '').strip()
    from_date = request.form.get('from_date', '').strip()
    to_date = request.form.get('to_date', '').strip()
    reason = request.form.get('reason', '').strip()

    # Validation
    if not all([name, from_date, to_date, reason]):
        flash('All fields are required!', 'warning')
        return redirect(url_for('index'))

    # Validate date order
    try:
        f = datetime.strptime(from_date, '%Y-%m-%d')
        t = datetime.strptime(to_date, '%Y-%m-%d')
        if t < f:
            flash('"From" date must be before or equal to "To" date.', 'warning')
            return redirect(url_for('index'))
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'warning')
        return redirect(url_for('index'))

    # Create new leave record with username
    new_leave = {
        'id': str(uuid.uuid4())[:8],
        'username': username,  # Track which user submitted this
        'name': name,
        'from_date': from_date,
        'to_date': to_date,
        'reason': reason,
        'status': 'pending',
        'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    leave_records.append(new_leave)
    flash('Leave application submitted successfully!', 'success')
    return redirect(url_for('list_leave'))

@app.route('/list')
@login_required
def list_leave():
    """Show leave applications for the logged-in user only"""
    username = session.get('username')
    user_leaves = [leave for leave in leave_records if leave['username'] == username]
    return render_template('list.html', leaves=user_leaves, user_name=session.get('user_name'))

# ------------------- Admin Routes -------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login successful! Welcome to the admin panel.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('admin_login.html')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('You have been logged out from admin panel.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard - view and manage all requests"""
    # Count statistics
    total = len(leave_records)
    pending = len([l for l in leave_records if l['status'] == 'pending'])
    approved = len([l for l in leave_records if l['status'] == 'approved'])
    rejected = len([l for l in leave_records if l['status'] == 'rejected'])
    
    # Get unique users
    unique_users = len(set([l['username'] for l in leave_records]))
    
    stats = {
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'users': unique_users
    }
    
    return render_template('admin_dashboard.html', leaves=leave_records, stats=stats)

@app.route('/admin/action/<leave_id>/<action>')
@admin_required
def admin_action(leave_id, action):
    """Approve or reject a leave request"""
    if action not in ('approve', 'reject'):
        flash('Invalid action.', 'warning')
        return redirect(url_for('admin_dashboard'))

    for leave in leave_records:
        if leave['id'] == leave_id:
            if leave['status'] != 'pending':
                flash(f'This request is already {leave["status"]}.', 'warning')
            else:
                leave['status'] = 'approved' if action == 'approve' else 'rejected'
                leave['reviewed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                flash(f'Leave {action}d successfully by admin.', 'success')
            break
    else:
        flash('Leave record not found.', 'warning')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<leave_id>')
@admin_required
def admin_delete(leave_id):
    """Delete a leave request (admin only)"""
    global leave_records
    for i, leave in enumerate(leave_records):
        if leave['id'] == leave_id:
            leave_records.pop(i)
            flash('Leave record deleted successfully.', 'success')
            break
    else:
        flash('Leave record not found.', 'warning')
    
    return redirect(url_for('admin_dashboard'))

# ------------------- Error Handlers -------------------

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Add a default admin user for testing
    if 'admin' not in users:
        users['admin'] = {
            'password': 'admin123',
            'name': 'Admin User',
            'email': 'admin@example.com',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    app.run(debug=True, port=5000)