from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from .models import get_db_connection
import sqlite3

main = Blueprint('main', __name__)

# ---------------------------
# Admin Login
@main.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admin WHERE email = ?', (email,)).fetchone()
        conn.close()

        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    # Ensure no cache for the login page
    response = make_response(render_template('admin/admin_login.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


# Admin Logout
@main.route('/logout')
def logout():
    session.clear()  # Clear session data
    flash('You have been logged out.', 'info')
    
    # After logout, ensure that the browser can't cache the login page
    response = make_response(redirect(url_for('main.login')))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response


# Admin Dashboard
@main.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    return render_template('admin/admin_dashboard.html')


# Admin creates a new user
@main.route('/create-user', methods=['GET', 'POST'])
def create_user():
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))

    message = None
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['useremail']
        password = request.form['userpassword']
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed_password))
            conn.commit()
            message = "✅ User created successfully."
        except sqlite3.IntegrityError:
            message = "⚠️ Email already exists."
        finally:
            conn.close()

    return render_template('admin/create_user.html', message=message)


# ---------------------------
# ✅ User Login
@main.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):  # user[3] is the password field
            session['user_id'] = user[0]      # assuming user[0] = id
            session['user_name'] = user[1]    # assuming user[1] = name
            return redirect(url_for('main.user_dashboard'))
        else:
            return render_template('user/user_login.html', error="Invalid email or password")

    # Ensure no cache for the login page
    response = make_response(render_template('user/user_login.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


# ✅ User Dashboard Route
@main.route('/user-dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.user_login'))
    
    # Prevent caching of this page by adding proper headers
    response = make_response(render_template('user/user_dashboard.html', user_name=session.get('user_name')))
    
    # Cache control headers
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


# ✅ User Logout Route
@main.route('/user-logout', methods=['POST'])
def user_logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'info')
    
    # After logout, ensure that the browser can't cache the login page
    response = make_response(redirect(url_for('main.user_login')))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response
