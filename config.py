
import os
import logging
from datetime import timedelta

def validate_environment():
    """Validate required environment variables"""
    required_vars = {
        'production': [
            'DATABASE_URL',
            'SECRET_KEY',
            'GCS_BUCKET_NAME',
            'GCS_PROJECT_ID'
        ],
        'development': [
            'SECRET_KEY'
        ]
    }
    
    env = os.environ.get('FLASK_ENV', 'production')
    missing_vars = []
    
    for var in required_vars.get(env, []):
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logging.warning(f"Missing environment variables for {env}: {', '.join(missing_vars)}")
        return False
    
    return True

# Validate environment on import
validate_environment()



import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 20,
        "max_overflow": 0
    }
    
    # File upload settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    UPLOAD_FOLDER = "uploads"
    REPORTS_FOLDER = "reports"
    
    # GCP Object Storage settings
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'fai-accountant-storage')
    GCS_PROJECT_ID = os.environ.get('GCS_PROJECT_ID', 'replit-gcs-project')
    GCS_REGION = os.environ.get('GCS_REGION', 'us-central1')
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Audit and compliance
    AUDIT_LOGGING_ENABLED = os.environ.get('AUDIT_LOGGING_ENABLED', 'true').lower() == 'true'
    RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', '2555'))  # 7 years
    ENCRYPTION_ENABLED = os.environ.get('ENCRYPTION_ENABLED', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///database/fai_accountant_dev.db'
    SESSION_COOKIE_SECURE = False
    
    # Local file storage for development
    USE_LOCAL_STORAGE = True
    LOCAL_STORAGE_PATH = "uploads"
    
    # Development database settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 20,
        "max_overflow": 0,
        "echo": True  # SQL logging for development
    }

class ProductionConfig(Config):
    """Production configuration for GCP deployment"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://fai_user:fai_password@0.0.0.0:5432/fai_accountant'
    
    # Production database settings with connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 30,
        "max_overflow": 10,
        "pool_size": 20,
        "echo": False
    }
    
    # Force HTTPS
    PREFERRED_URL_SCHEME = 'https'
    
    # GCP Object Storage
    USE_GCP_STORAGE = True
    
    # Enhanced security
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    
    # Logging
    LOG_LEVEL = 'INFO'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    USE_LOCAL_STORAGE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
