from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from .models import add_subject, get_subjects_for_user, update_subject, Admin, User
from .models import db  # ✅ Add this if it's missing


import sqlite3

main = Blueprint('main', __name__)

# ---------------------------
# Admin Login
from .models import Admin  # make sure this is imported at the top

@main.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        admin = Admin.query.filter_by(email=email).first()

        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
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
from .models import User  # make sure it's already imported

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

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            message = "⚠️ Email already exists."
        else:
            new_user = User(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            message = "✅ User created successfully."

    return render_template('admin/create_user.html', message=message)


# ---------------------------
# ✅ User Login
@main.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('main.user_dashboard'))
        else:
            return render_template('user/user_login.html', error="Invalid email or password")

    response = make_response(render_template('user/user_login.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ✅ User Dashboard Route
from .models import Subject  # already imported earlier

@main.route('/user-dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.user_login'))

    user_id = session['user_id']
    subjects = Subject.query.filter_by(user_id=user_id).all()

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
    new_subject = Subject(user_id=user_id, name=subject_name)
    db.session.add(new_subject)
    db.session.commit()

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

    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first()
    if subject:
        subject.name = new_name
        db.session.commit()
        return jsonify({'message': 'Subject updated successfully'})
    else:
        return jsonify({'error': 'Subject not found'}), 404


# ✅ Delete Subject API Route (Bulk Delete)
@main.route('/delete_subjects', methods=['POST'])
def delete_subjects_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    subject_ids = data.get('subject_ids')

    if not subject_ids or not isinstance(subject_ids, list):
        return jsonify({'error': 'Invalid input'}), 400

    Subject.query.filter(Subject.id.in_(subject_ids), Subject.user_id == session['user_id']).delete(synchronize_session=False)
    db.session.commit()

    return jsonify({'message': 'Subjects deleted successfully'})



@main.route('/subject/<int:subject_id>')
def subject_detail(subject_id):
    if 'user_id' not in session:
        return redirect(url_for('main.user_login'))

    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first()

    if not subject:
        return "Subject not found", 404

    return render_template(
        'user/subject_detail.html',
        subject=subject,
        user_name=session.get('user_name')
    )

