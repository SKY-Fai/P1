from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
import os
import logging
from datetime import datetime
import json

# Import your modules
from app import create_app, db
from models import User, Company, UserCompanyAccess, AuditLog
from auth import auth_bp
from routes import main_bp  
from admin_routes import admin_bp
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_application():
    """Create and configure the Flask application"""
    try:
        app = create_app()

        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(main_bp)
        app.register_blueprint(admin_bp, url_prefix='/admin')

        # Create database tables
        with app.app_context():
            db.create_all()

            # Create default admin user if it doesn't exist
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@f-ai.com',
                    password_hash=generate_password_hash('admin123'),
                    user_category='admin',
                    is_active=True
                )
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Default admin user created")

        return app

    except Exception as e:
        logger.error(f"Error creating application: {str(e)}")
        raise

# Create the application
app = create_application()

if __name__ == '__main__':
    try:
        # Ensure directories exist
        os.makedirs('logs', exist_ok=True)
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('reports', exist_ok=True)

        logger.info("Starting F-AI Accountant Server...")
        logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")

        # Run the application
        app.run(host='0.0.0.0', port=5000, debug=True)

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise