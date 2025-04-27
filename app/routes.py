from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response, jsonify, current_app, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import io
import zipfile
from .models import add_subject, get_all_subjects, update_subject, Admin, User, Subject, Content, db, create_content

main = Blueprint('main', __name__)

# ---------------------------
# Admin Login
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
@main.route('/user-dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.user_login'))

    subjects = get_all_subjects()

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

    add_subject(subject_name)
    return jsonify({'message': 'Subject added successfully'})

# ✅ Update Subject API Route
@main.route('/update_subject', methods=['POST'])
def update_subject_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    subject_id = data.get('subject_id')
    new_name = data.get('subject_name')

    if not subject_id or not new_name:
        return jsonify({'error': 'Missing data'}), 400

    subject = Subject.query.filter_by(id=subject_id).first()
    if subject:
        subject.name = new_name
        db.session.commit()
        return jsonify({'message': 'Subject updated successfully'})
    else:
        return jsonify({'error': 'Subject not found'}), 404

# ✅ Delete Subject API Route
@main.route('/delete_subjects', methods=['POST'])
def delete_subjects_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    subject_ids = data.get('subject_ids')

    if not subject_ids or not isinstance(subject_ids, list):
        return jsonify({'error': 'Invalid input'}), 400

    Subject.query.filter(Subject.id.in_(subject_ids)).delete(synchronize_session=False)
    db.session.commit()

    return jsonify({'message': 'Subjects deleted successfully'})

# ✅ Subject Detail Page
@main.route('/subject/<int:subject_id>')
def subject_detail(subject_id):
    if 'user_id' not in session:
        return redirect(url_for('main.user_login'))

    subject = Subject.query.filter_by(id=subject_id).first()

    if not subject:
        return "Subject not found", 404

    # ✅ Fetch uploaded files for this subject
    uploaded_files = Content.query.filter_by(subject_id=subject_id).all()

    return render_template(
        'user/subject_detail.html',
        subject=subject,
        uploaded_files=uploaded_files,
        user_name=session.get('user_name')
    )

# ✅ Step 2: Upload Content (File Upload Route)
@main.route('/upload_content/<int:subject_id>', methods=['POST'])
def upload_content(subject_id):
    if 'files' not in request.files:
        return 'No file part', 400

    files = request.files.getlist('files')

    for file in files:
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)

            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(subject_id))
            os.makedirs(upload_folder, exist_ok=True)

            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            create_content(subject_id, filename, "Uploaded PDF", file_path)

    return redirect(url_for('main.subject_detail', subject_id=subject_id))

# ✅ Delete File
@main.route('/delete_file/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    if 'user_id' not in session:
        return redirect(url_for('main.user_login'))

    file_record = Content.query.get(file_id)

    if not file_record:
        return 'File not found', 404

    # Delete the file from storage
    if file_record.file_path and os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)

    # Delete the database record
    db.session.delete(file_record)
    db.session.commit()

    return redirect(url_for('main.subject_detail', subject_id=file_record.subject_id))

# ✨ ✅ New Download Subjects Route
@main.route('/download_subjects', methods=['POST'])
def download_subjects():
    subject_ids = request.form.getlist('subject_ids')

    if not subject_ids:
        return "No subjects selected.", 400

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for subject_id in subject_ids:
            subject = Subject.query.get(subject_id)
            if not subject:
                continue

            contents = Content.query.filter_by(subject_id=subject_id).all()

            for content in contents:
                file_path = content.file_path
                if file_path and os.path.exists(file_path):
                    subject_folder = secure_filename(subject.name)
                    file_name = os.path.basename(file_path)
                    arcname = os.path.join(subject_folder, file_name)
                    zipf.write(file_path, arcname=arcname)

    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype='application/zip',
        download_name='selected_subjects.zip',
        as_attachment=True
    )





@main.route('/')
def home():
    return redirect(url_for('main.user_login'))

