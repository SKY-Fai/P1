
#!/usr/bin/env python3
"""
Production Database Setup for F-AI Accountant
Supports both PostgreSQL (production) and SQLite (development)
"""

import os
import sys
import logging
import psycopg2
import sqlite3
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import config

class ProductionDatabaseSetup:
    """Production-ready database setup and management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_name = os.environ.get('FLASK_ENV', 'production')
        self.config = config.get(self.config_name, config['production'])
        
    def setup_postgresql_production(self):
        """Setup PostgreSQL for production deployment"""
        self.logger.info("Setting up PostgreSQL for production...")
        
        try:
            # Parse database URL
            db_url = self.config.SQLALCHEMY_DATABASE_URI
            if not db_url.startswith('postgresql://'):
                self.logger.error("PostgreSQL URL required for production")
                return False
            
            # Connect to PostgreSQL
            conn = psycopg2.connect(db_url)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Execute production schema
            schema_file = Path(__file__).parent / 'production_schema.sql'
            if schema_file.exists():
                with open(schema_file, 'r') as f:
                    cursor.execute(f.read())
            else:
                # Create basic schema if file doesn't exist
                self._create_production_schema(cursor)
            
            # Insert production data
            self._insert_production_data(cursor)
            
            cursor.close()
            conn.close()
            
            self.logger.info("✅ PostgreSQL production setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ PostgreSQL setup failed: {e}")
            return False
    
    def setup_sqlite_development(self):
        """Setup SQLite for development"""
        self.logger.info("Setting up SQLite for development...")
        
        try:
            db_path = "database/fai_accountant_dev.db"
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create development schema
            self._create_development_schema(cursor)
            
            # Insert development data
            self._insert_development_data(cursor)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info("✅ SQLite development setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ SQLite setup failed: {e}")
            return False
    
    def _create_production_schema(self, cursor):
        """Create production database schema"""
        
        # Enhanced users table for production
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                category VARCHAR(20) DEFAULT 'individual',
                user_code VARCHAR(20) UNIQUE,
                access_code VARCHAR(10),
                parent_user_id INTEGER REFERENCES users(id),
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                role VARCHAR(20) DEFAULT 'viewer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Companies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                registration_number VARCHAR(100) UNIQUE,
                tax_id VARCHAR(100) UNIQUE,
                address TEXT,
                phone VARCHAR(20),
                email VARCHAR(120),
                owner_user_id INTEGER NOT NULL REFERENCES users(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # File storage metadata (GCP integration)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_storage_metadata (
                id SERIAL PRIMARY KEY,
                file_path VARCHAR(1000) NOT NULL UNIQUE,
                original_filename VARCHAR(500) NOT NULL,
                secure_filename VARCHAR(500) NOT NULL,
                file_hash VARCHAR(64) NOT NULL,
                file_size BIGINT NOT NULL,
                mime_type VARCHAR(200),
                content_type VARCHAR(200),
                user_id INTEGER NOT NULL REFERENCES users(id),
                organization_id INTEGER REFERENCES companies(id),
                file_category VARCHAR(50) DEFAULT 'other',
                storage_bucket VARCHAR(200) DEFAULT 'fai-accountant-storage',
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_encrypted BOOLEAN DEFAULT TRUE,
                is_deleted BOOLEAN DEFAULT FALSE,
                processing_status VARCHAR(50) DEFAULT 'uploaded'
            )
        ''')
        
        # Chart of accounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chart_of_accounts (
                id SERIAL PRIMARY KEY,
                company_id INTEGER REFERENCES companies(id),
                account_code VARCHAR(20) NOT NULL,
                account_name VARCHAR(200) NOT NULL,
                account_type VARCHAR(50) NOT NULL,
                parent_account_id INTEGER REFERENCES chart_of_accounts(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Journal entries with enhanced workflow
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                id SERIAL PRIMARY KEY,
                company_id INTEGER REFERENCES companies(id),
                account_id INTEGER REFERENCES chart_of_accounts(id),
                created_by INTEGER REFERENCES users(id),
                entry_date TIMESTAMP NOT NULL,
                description TEXT NOT NULL,
                reference_number VARCHAR(100),
                debit_amount DECIMAL(15,2) DEFAULT 0.00,
                credit_amount DECIMAL(15,2) DEFAULT 0.00,
                status VARCHAR(20) DEFAULT 'draft',
                is_posted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Audit log for compliance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                table_name VARCHAR(100),
                record_id INTEGER,
                old_values JSONB,
                new_values JSONB,
                ip_address INET,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_storage_user ON file_storage_metadata(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(entry_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)')
        
        self.logger.info("✅ Production schema created")
    
    def _create_development_schema(self, cursor):
        """Create development database schema (SQLite)"""
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                category TEXT DEFAULT 'individual',
                user_code TEXT UNIQUE,
                access_code TEXT,
                parent_user_id INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                role TEXT DEFAULT 'viewer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_user_id) REFERENCES users(id)
            )
        ''')
        
        # Companies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                registration_number TEXT UNIQUE,
                address TEXT,
                phone TEXT,
                email TEXT,
                owner_user_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_user_id) REFERENCES users(id)
            )
        ''')
        
        # Chart of accounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chart_of_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_code TEXT UNIQUE NOT NULL,
                account_name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                parent_account_id INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_account_id) REFERENCES chart_of_accounts(id)
            )
        ''')
        
        # Journal entries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                entry_date TIMESTAMP NOT NULL,
                description TEXT NOT NULL,
                reference_number TEXT,
                debit_amount DECIMAL(15,2) DEFAULT 0.00,
                credit_amount DECIMAL(15,2) DEFAULT 0.00,
                status TEXT DEFAULT 'draft',
                is_posted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        self.logger.info("✅ Development schema created")
    
    def _insert_production_data(self, cursor):
        """Insert production default data"""
        
        # Default admin user for production
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name, role)
            VALUES ('admin', 'admin@fai-accountant.com', 'pbkdf2:sha256:600000$production', 'System', 'Administrator', 'admin')
            ON CONFLICT (email) DO NOTHING
        ''')
        
        # Standard chart of accounts
        accounts = [
            ('1000', 'Assets', 'asset'),
            ('1100', 'Current Assets', 'asset'),
            ('1110', 'Cash and Cash Equivalents', 'asset'),
            ('1120', 'Accounts Receivable', 'asset'),
            ('2000', 'Liabilities', 'liability'),
            ('2100', 'Current Liabilities', 'liability'),
            ('2110', 'Accounts Payable', 'liability'),
            ('3000', 'Equity', 'equity'),
            ('3100', 'Share Capital', 'equity'),
            ('4000', 'Revenue', 'revenue'),
            ('4100', 'Sales Revenue', 'revenue'),
            ('5000', 'Expenses', 'expense'),
            ('5100', 'Operating Expenses', 'expense')
        ]
        
        for account_code, account_name, account_type in accounts:
            cursor.execute('''
                INSERT INTO chart_of_accounts (account_code, account_name, account_type)
                VALUES (%s, %s, %s)
                ON CONFLICT (account_code) DO NOTHING
            ''', (account_code, account_name, account_type))
        
        self.logger.info("✅ Production data inserted")
    
    def _insert_development_data(self, cursor):
        """Insert development test data"""
        
        # Development admin user
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, first_name, last_name, role)
            VALUES ('admin', 'admin@fai-accountant.com', 'pbkdf2:sha256:260000$development', 'Admin', 'User', 'admin')
        ''')
        
        # Test company
        cursor.execute('''
            INSERT OR IGNORE INTO companies (name, registration_number, owner_user_id)
            VALUES ('F-AI Test Company', 'TEST123456', 1)
        ''')
        
        # Basic chart of accounts
        accounts = [
            ('1000', 'Assets', 'asset'),
            ('1100', 'Cash', 'asset'),
            ('2000', 'Liabilities', 'liability'),
            ('2100', 'Accounts Payable', 'liability'),
            ('3000', 'Equity', 'equity'),
            ('4000', 'Revenue', 'revenue'),
            ('5000', 'Expenses', 'expense')
        ]
        
        for account_code, account_name, account_type in accounts:
            cursor.execute('''
                INSERT OR IGNORE INTO chart_of_accounts (account_code, account_name, account_type)
                VALUES (?, ?, ?)
            ''', (account_code, account_name, account_type))
        
        self.logger.info("✅ Development data inserted")
    
    def run_setup(self):
        """Run appropriate setup based on environment"""
        env = os.environ.get('FLASK_ENV', 'production')
        
        if env == 'production':
            return self.setup_postgresql_production()
        else:
            return self.setup_sqlite_development()

def main():
    """Main setup function"""
    logging.basicConfig(level=logging.INFO)
    
    setup = ProductionDatabaseSetup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'production':
            os.environ['FLASK_ENV'] = 'production'
        elif command == 'development':
            os.environ['FLASK_ENV'] = 'development'
    
    success = setup.run_setup()
    
    if success:
        print("✅ Database setup completed successfully")
        return 0
    else:
        print("❌ Database setup failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
