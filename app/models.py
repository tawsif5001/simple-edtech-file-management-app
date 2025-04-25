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

# ✅ Subject model
class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', backref=db.backref('subjects', lazy=True))


# ✅ Utility functions (used in routes)

def add_subject(user_id, name):
    subject = Subject(user_id=user_id, name=name)
    db.session.add(subject)
    db.session.commit()

def get_subjects_for_user(user_id):
    return Subject.query.filter_by(user_id=user_id).all()

def update_subject(subject_id, user_id, new_name):
    subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
    if subject:
        subject.name = new_name
        db.session.commit()
