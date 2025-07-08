#!/usr/bin/env python3
"""
F-AI Accountant Database Manager
Comprehensive database management system with local setup
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2 import sql
import subprocess
import json
import shutil
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Comprehensive database management for F-AI Accountant"""
    
    def __init__(self):
        self.db_dir = Path("database")
        self.db_dir.mkdir(exist_ok=True)
        self.sqlite_db = self.db_dir / "fai_accountant.db"
        self.backup_dir = self.db_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def setup_sqlite(self):
        """Setup SQLite database for local development"""
        logger.info("Setting up SQLite database...")
        
        try:
            conn = sqlite3.connect(str(self.sqlite_db))
            cursor = conn.cursor()
            
            # Create tables
            self.create_sqlite_tables(cursor)
            
            # Insert default data
            self.insert_default_data_sqlite(cursor)
            
            conn.commit()
            conn.close()
            
            logger.info("✅ SQLite database setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ SQLite setup failed: {e}")
            return False
    
    def create_sqlite_tables(self, cursor):
        """Create all necessary tables for SQLite"""
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                first_name TEXT,
                last_name TEXT,
                profile_image_url TEXT,
                user_code TEXT UNIQUE,
                access_code TEXT,
                login_link TEXT,
                base_user_code TEXT,
                parent_user_id INTEGER,
                category TEXT DEFAULT 'individual',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_user_id) REFERENCES users(id)
            )
        ''')
        
        # Companies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                registration_number TEXT UNIQUE,
                company_type TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                gstin TEXT,
                pan TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # Chart of Accounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chart_of_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_code TEXT UNIQUE NOT NULL,
                account_name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                parent_account TEXT,
                balance DECIMAL(15,2) DEFAULT 0.00,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Journal Entries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_number TEXT NOT NULL,
                entry_date DATE NOT NULL,
                description TEXT,
                account_code TEXT NOT NULL,
                account_name TEXT NOT NULL,
                entry_type TEXT NOT NULL CHECK (entry_type IN ('debit', 'credit')),
                amount DECIMAL(15,2) NOT NULL,
                status TEXT DEFAULT 'draft',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                posted_at TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (account_code) REFERENCES chart_of_accounts(account_code)
            )
        ''')
        
        # Invoices
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                invoice_date DATE NOT NULL,
                due_date DATE,
                customer_name TEXT NOT NULL,
                customer_email TEXT,
                customer_address TEXT,
                subtotal DECIMAL(15,2) NOT NULL,
                tax_amount DECIMAL(15,2) DEFAULT 0.00,
                total_amount DECIMAL(15,2) NOT NULL,
                status TEXT DEFAULT 'draft',
                payment_status TEXT DEFAULT 'pending',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # Uploaded Files
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                template_type TEXT,
                status TEXT DEFAULT 'uploaded',
                user_id INTEGER,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Processing Results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                result_type TEXT NOT NULL,
                result_data TEXT,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES uploaded_files(id)
            )
        ''')
        
        # Audit Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Bank Transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bank_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date DATE NOT NULL,
                description TEXT NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                balance DECIMAL(15,2),
                reference_number TEXT,
                account_number TEXT,
                transaction_type TEXT,
                status TEXT DEFAULT 'unmatched',
                matched_invoice_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (matched_invoice_id) REFERENCES invoices(id)
            )
        ''')
        
        # Financial Reports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                report_data TEXT,
                generated_by INTEGER,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (generated_by) REFERENCES users(id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(entry_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_uploaded_files_user ON uploaded_files(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)')
        
        logger.info("✅ SQLite tables created successfully")
    
    def insert_default_data_sqlite(self, cursor):
        """Insert default data into SQLite database"""
        
        # Default admin user
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, role, first_name, last_name)
            VALUES ('admin', 'admin@fai-accountant.com', 'pbkdf2:sha256:260000$test', 'admin', 'Admin', 'User')
        ''')
        
        # Default chart of accounts
        accounts = [
            ('1000', 'Assets', 'asset', None),
            ('1100', 'Current Assets', 'asset', '1000'),
            ('1110', 'Cash and Cash Equivalents', 'asset', '1100'),
            ('1120', 'Accounts Receivable', 'asset', '1100'),
            ('1130', 'Inventory', 'asset', '1100'),
            ('1200', 'Non-Current Assets', 'asset', '1000'),
            ('1210', 'Property, Plant & Equipment', 'asset', '1200'),
            ('2000', 'Liabilities', 'liability', None),
            ('2100', 'Current Liabilities', 'liability', '2000'),
            ('2110', 'Accounts Payable', 'liability', '2100'),
            ('2120', 'Short-term Debt', 'liability', '2100'),
            ('2200', 'Non-Current Liabilities', 'liability', '2000'),
            ('2210', 'Long-term Debt', 'liability', '2200'),
            ('3000', 'Equity', 'equity', None),
            ('3100', 'Share Capital', 'equity', '3000'),
            ('3200', 'Retained Earnings', 'equity', '3000'),
            ('4000', 'Revenue', 'revenue', None),
            ('4100', 'Sales Revenue', 'revenue', '4000'),
            ('4200', 'Service Revenue', 'revenue', '4000'),
            ('5000', 'Expenses', 'expense', None),
            ('5100', 'Cost of Goods Sold', 'expense', '5000'),
            ('5200', 'Operating Expenses', 'expense', '5000'),
            ('5210', 'Salaries and Wages', 'expense', '5200'),
            ('5220', 'Rent Expense', 'expense', '5200'),
            ('5230', 'Utilities Expense', 'expense', '5200'),
            ('5240', 'Professional Fees', 'expense', '5200')
        ]
        
        for account in accounts:
            cursor.execute('''
                INSERT OR IGNORE INTO chart_of_accounts (account_code, account_name, account_type, parent_account)
                VALUES (?, ?, ?, ?)
            ''', account)
        
        logger.info("✅ Default data inserted successfully")
    
    def setup_postgresql(self, host='localhost', port=5432, user='fai_user', password='fai_password', database='fai_accountant'):
        """Setup PostgreSQL database"""
        logger.info("Setting up PostgreSQL database...")
        
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            
            cursor = conn.cursor()
            
            # Execute initialization script
            with open('database/init.sql', 'r') as f:
                cursor.execute(f.read())
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ PostgreSQL database setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL setup failed: {e}")
            return False
    
    def create_backup(self, backup_name=None):
        """Create database backup"""
        if backup_name is None:
            backup_name = f"fai_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / f"{backup_name}.db"
        
        try:
            shutil.copy2(self.sqlite_db, backup_path)
            logger.info(f"✅ Backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """Restore database from backup"""
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.sqlite_db)
                logger.info(f"✅ Database restored from: {backup_path}")
                return True
            else:
                logger.error(f"❌ Backup file not found: {backup_path}")
                return False
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    def get_database_info(self):
        """Get database information"""
        try:
            conn = sqlite3.connect(str(self.sqlite_db))
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            info = {
                'database_type': 'SQLite',
                'database_path': str(self.sqlite_db),
                'tables': [table[0] for table in tables],
                'database_size': os.path.getsize(self.sqlite_db) if os.path.exists(self.sqlite_db) else 0
            }
            
            cursor.close()
            conn.close()
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Failed to get database info: {e}")
            return None
    
    def cleanup_old_backups(self, keep_days=30):
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for backup_file in self.backup_dir.glob("*.db"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    logger.info(f"🗑️  Deleted old backup: {backup_file}")
            
            logger.info("✅ Backup cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Backup cleanup failed: {e}")

def main():
    """Main function for database management"""
    db_manager = DatabaseManager()
    
    print("=" * 60)
    print("🗄️  F-AI ACCOUNTANT DATABASE MANAGER")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("Usage: python database_manager.py <command>")
        print("Commands:")
        print("  setup      - Setup SQLite database")
        print("  backup     - Create database backup")
        print("  restore    - Restore from backup")
        print("  info       - Show database information")
        print("  cleanup    - Cleanup old backups")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "setup":
        if db_manager.setup_sqlite():
            print("✅ Database setup completed successfully")
        else:
            print("❌ Database setup failed")
    
    elif command == "backup":
        backup_path = db_manager.create_backup()
        if backup_path:
            print(f"✅ Backup created: {backup_path}")
        else:
            print("❌ Backup failed")
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Usage: python database_manager.py restore <backup_path>")
            sys.exit(1)
        
        backup_path = sys.argv[2]
        if db_manager.restore_backup(backup_path):
            print("✅ Database restored successfully")
        else:
            print("❌ Restore failed")
    
    elif command == "info":
        info = db_manager.get_database_info()
        if info:
            print(f"Database Type: {info['database_type']}")
            print(f"Database Path: {info['database_path']}")
            print(f"Database Size: {info['database_size']} bytes")
            print(f"Tables: {', '.join(info['tables'])}")
        else:
            print("❌ Failed to get database information")
    
    elif command == "cleanup":
        db_manager.cleanup_old_backups()
        print("✅ Backup cleanup completed")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()