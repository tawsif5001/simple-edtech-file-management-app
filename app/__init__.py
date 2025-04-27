from flask import Flask
from .models import db  # ✅ Use the shared db instance

def create_app():
    app = Flask(__name__)
    
    app.secret_key = 'your_secret_key_here'

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://freedb_mytestuser:Test@12345@sql.freedb.tech/freedb_mytestdb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the shared database instance
    db.init_app(app)

    # Import and register Blueprints
    from .routes import main
    app.register_blueprint(main)

    return app
