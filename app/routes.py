from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from .models import get_db_connection, add_subject, get_subjects_for_user, update_subject  # ✅ included update_subject
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

    response = make_response(render_template('admin/admin_login.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Admin Logout
@main.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
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

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect(url_for('main.user_dashboard'))
        else:
            return render_template('user/user_login.html', error="Invalid email or password")

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

    user_id = session['user_id']
    subjects = get_subjects_for_user(user_id)

    response = make_response(render_template(
        'user/user_dashboard.html',
        user_name=session.get('user_name'),
        subjects=subjects
    ))

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

    response = make_response(redirect(url_for('main.user_login')))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ✅ Add Subject API Route
@main.route('/add_subject', methods=['POST'])
def add_subject_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    subject_name = data.get('subject_name')

    if not subject_name:
        return jsonify({'error': 'Subject name is required'}), 400

    user_id = session['user_id']
    add_subject(user_id, subject_name)

    return jsonify({'message': 'Subject added successfully'})

# ✅ Update Subject API Route (Step 2)
@main.route('/update_subject', methods=['POST'])
def update_subject_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    subject_id = data.get('subject_id')
    new_name = data.get('subject_name')

    if not subject_id or not new_name:
        return jsonify({'error': 'Missing data'}), 400

    update_subject(subject_id, session['user_id'], new_name)
    return jsonify({'message': 'Subject updated successfully'})

# ✅ Delete Subject API Route (Bulk Delete)
@main.route('/delete_subjects', methods=['POST'])
def delete_subjects_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    subject_ids = data.get('subject_ids')

    if not subject_ids or not isinstance(subject_ids, list):
        return jsonify({'error': 'Invalid input'}), 400

    conn = get_db_connection()
    conn.executemany(
        'DELETE FROM subjects WHERE id = ? AND user_id = ?',
        [(sub_id, session['user_id']) for sub_id in subject_ids]
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Subjects deleted successfully'})

