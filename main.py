#!/usr/bin/env python3
"""
F-AI Accountant - Production Ready Flask Application
Enterprise Accounting SaaS Platform with GCP Integration
"""

import os
import sys
import logging
import socket
import time
from datetime import datetime
from flask import Flask
from flask_migrate import Migrate
from config import config
from app import create_app, db

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[

import time

def validate_critical_services(app):
    """Validate that critical services are available"""
    with app.app_context():
        try:
            # Test database connectivity
            db.session.execute('SELECT 1')
            logging.info("✓ Database connectivity verified")
            
            # Test file system permissions
            test_file = 'uploads/.test_write'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logging.info("✓ File system write permissions verified")
            
            # Test GCP storage if enabled
            if app.config.get('USE_GCP_STORAGE'):
                try:
                    from services.gcp_storage_service import GCPStorageService
                    storage = GCPStorageService()
                    if storage.client:
                        logging.info("✓ GCP Storage service verified")
                    else:
                        logging.warning("⚠ GCP Storage service not available")
                except Exception as e:
                    logging.warning(f"⚠ GCP Storage validation failed: {e}")
                    
        except Exception as e:
            logging.error(f"Critical service validation failed: {e}")
            raise


        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log') if os.path.exists('logs') else logging.StreamHandler()
    ]
)

def create_production_app():
    """Create and configure the Flask application for production"""
    try:
        # Determine configuration
        config_name = os.environ.get('FLASK_ENV', 'production')
        if config_name not in config:
            config_name = 'production'
            logging.warning(f"Unknown FLASK_ENV, defaulting to production")

        # Create app with configuration
        app = create_app()
        app.config.from_object(config[config_name])

        # Setup database migrations
        migrate = Migrate(app, db)

        # Create necessary directories with proper error handling
        directories = ['uploads', 'reports', 'logs', 'temp', 'static/uploads', 'database/backups']
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                logging.info(f"Directory created/verified: {directory}")
            except PermissionError as e:
                logging.error(f"Permission denied creating directory {directory}: {e}")
                raise
            except Exception as e:
                logging.error(f"Failed to create directory {directory}: {e}")
                raise

        # Initialize database with retry logic
        with app.app_context():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Test database connection first
                    db.session.execute('SELECT 1')
                    db.create_all()
                    logging.info("Database tables created successfully")
                    break
                except Exception as e:
                    logging.error(f"Database initialization attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        logging.critical("Database initialization failed after all retries")
                        raise
                    time.sleep(2)

        # Register error handlers
        register_error_handlers(app)

        # Validate critical services
        validate_critical_services(app)

        return app
        
    except Exception as e:
        logging.critical(f"Failed to create production app: {e}")
        raise

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
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": "2.0.0",
        "environment": os.environ.get('FLASK_ENV', 'production'),
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    try:
        # Database connectivity check
        start_time = time.time()
        db.session.execute('SELECT 1')
        db_response_time = (time.time() - start_time) * 1000
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_response_time, 2)
        }
        
        # File system check
        try:
            test_file = 'uploads/.health_check'
            with open(test_file, 'w') as f:
                f.write('health_check')
            os.remove(test_file)
            health_status["checks"]["filesystem"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["filesystem"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # GCP Storage check (if enabled)
        if app.config.get('USE_GCP_STORAGE'):
            try:
                from services.gcp_storage_service import GCPStorageService
                storage = GCPStorageService()
                if storage.client and storage.bucket.exists():
                    health_status["checks"]["gcp_storage"] = {"status": "healthy"}
                else:
                    health_status["checks"]["gcp_storage"] = {"status": "unhealthy"}
                    health_status["status"] = "degraded"
            except Exception as e:
                health_status["checks"]["gcp_storage"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
        
        # Overall status determination
        failed_checks = [check for check in health_status["checks"].values() if check["status"] != "healthy"]
        if failed_checks:
            health_status["status"] = "degraded" if len(failed_checks) < len(health_status["checks"]) else "unhealthy"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return health_status, status_code
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, 503

if __name__ == "__main__":
    # Production server configuration
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    debug = os.environ.get('FLASK_ENV') == 'development'

    # Validate port availability
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        if result == 0:
            logging.warning(f"Port {port} is already in use")
        sock.close()
    except Exception as e:
        logging.warning(f"Port check failed: {e}")

    if debug:
        # Development mode
        logging.info(f"Starting development server on {host}:{port}")
        app.run(host=host, port=port, debug=True, threaded=True)
    else:
        # Production mode - try Gunicorn first, fallback to Flask
        try:
            import gunicorn
            import subprocess
            
            gunicorn_cmd = [
                sys.executable, "-m", "gunicorn",
                "--bind", f"{host}:{port}",
                "--workers", str(os.cpu_count() or 4),
                "--worker-class", "sync",
                "--timeout", "300",
                "--keep-alive", "2",
                "--max-requests", "1000",
                "--max-requests-jitter", "100",
                "--preload",
                "--access-logfile", "-",
                "--error-logfile", "-",
                "main:app"
            ]

            logging.info(f"Starting Gunicorn server on {host}:{port}")
            subprocess.run(gunicorn_cmd, check=True)
            
        except (ImportError, subprocess.CalledProcessError) as e:
            logging.warning(f"Gunicorn unavailable or failed: {e}")
            logging.info(f"Falling back to Flask development server on {host}:{port}")
            app.run(host=host, port=port, debug=False, threaded=True)