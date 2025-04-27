from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ✅ User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# ✅ Admin model
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# ✅ Subject model (now global for all users)
class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

# ✅ Content model (for uploaded files)
class Content(db.Model):
    __tablename__ = 'content'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)

# ✅ Utility functions (used in routes)

def add_subject(name):
    subject = Subject(name=name)
    db.session.add(subject)
    db.session.commit()

def get_all_subjects():
    return Subject.query.all()

def update_subject(subject_id, new_name):
    subject = Subject.query.filter_by(id=subject_id).first()
    if subject:
        subject.name = new_name
        db.session.commit()

# ✅ create_content function (for uploading files)
def create_content(subject_id, file_name, description, file_path):
    new_content = Content(subject_id=subject_id, file_name=file_name, description=description, file_path=file_path)
    db.session.add(new_content)
    db.session.commit()
