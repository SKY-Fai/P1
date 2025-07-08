#!/usr/bin/env python3
"""
F-AI Accountant - Production Ready Flask Application
Enterprise Accounting SaaS Platform with GCP Integration
"""

import os
import sys
import logging
from flask import Flask
from flask_migrate import Migrate
from config import config
from app import create_app, db

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log') if os.path.exists('logs') else logging.StreamHandler()
    ]
)

def create_production_app():
    """Create and configure the Flask application for production"""
    # Determine configuration
    config_name = os.environ.get('FLASK_ENV', 'production')
    if config_name not in config:
        config_name = 'production'

    # Create app with configuration
    app = create_app()
    app.config.from_object(config[config_name])

    # Setup database migrations
    migrate = Migrate(app, db)

    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    # Initialize database
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")

    # Register error handlers
    register_error_handlers(app)

    return app

def register_error_handlers(app):
    """Register production error handlers"""
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Resource not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {"error": "Internal server error"}, 500

    @app.errorhandler(413)
    def too_large(error):
        return {"error": "File too large"}, 413

# Create the application
app = create_production_app()

# Health check endpoint for production monitoring
@app.route('/health')
def health_check():
    """Health check endpoint for load balancer"""
    try:
        # Test database connectivity
        db.session.execute('SELECT 1')
        return {
            "status": "healthy",
            "version": "2.0.0",
            "environment": os.environ.get('FLASK_ENV', 'production')
        }, 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}, 503

if __name__ == "__main__":
    # Production server configuration
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    debug = os.environ.get('FLASK_ENV') == 'development'

    if debug:
        # Development mode
        app.run(host=host, port=port, debug=True)
    else:
        # Production mode with Gunicorn
        import subprocess
        import sys

        gunicorn_cmd = [
            sys.executable, "-m", "gunicorn",
            "--bind", f"{host}:{port}",
            "--workers", "4",
            "--worker-class", "sync",
            "--timeout", "300",
            "--keep-alive", "2",
            "--max-requests", "1000",
            "--max-requests-jitter", "100",
            "--preload",
            "main:app"
        ]

        try:
            subprocess.run(gunicorn_cmd, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Gunicorn failed to start: {e}")
            # Fallback to development server
            app.run(host=host, port=port, debug=False)