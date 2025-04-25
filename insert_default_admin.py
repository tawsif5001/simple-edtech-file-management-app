from app import create_app
from app.models import db, Admin
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Check if the admin already exists
    existing_admin = Admin.query.filter_by(email='admin@example.com').first()
    
    if not existing_admin:
        default_admin = Admin(
            email='admin@example.com',
            password=generate_password_hash('admin123', method='pbkdf2:sha256')
        )
        db.session.add(default_admin)
        db.session.commit()
        print("✅ Default admin created!")
    else:
        print("⚠️ Default admin already exists.")

