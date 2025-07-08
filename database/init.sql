-- F-AI Accountant Database Initialization Script
-- PostgreSQL Database Setup

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS fai_accountant;

-- Use the database
\c fai_accountant;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS accounting;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS reports;
CREATE SCHEMA IF NOT EXISTS templates;

-- Set search path
SET search_path TO public, accounting, audit, reports, templates;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_user ON uploaded_files(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);

-- Create views for reporting
CREATE OR REPLACE VIEW accounting.trial_balance AS
SELECT 
    account_name,
    SUM(CASE WHEN entry_type = 'debit' THEN amount ELSE 0 END) as debit_total,
    SUM(CASE WHEN entry_type = 'credit' THEN amount ELSE 0 END) as credit_total,
    SUM(CASE WHEN entry_type = 'debit' THEN amount ELSE -amount END) as balance
FROM journal_entries
GROUP BY account_name;

CREATE OR REPLACE VIEW reports.monthly_summary AS
SELECT 
    DATE_TRUNC('month', entry_date) as month,
    account_name,
    SUM(amount) as total_amount,
    COUNT(*) as transaction_count
FROM journal_entries
GROUP BY DATE_TRUNC('month', entry_date), account_name;

-- Create functions for data integrity
CREATE OR REPLACE FUNCTION check_double_entry()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if total debits equal total credits for the same reference
    IF (SELECT SUM(CASE WHEN entry_type = 'debit' THEN amount ELSE -amount END) 
        FROM journal_entries 
        WHERE reference_number = NEW.reference_number) != 0 THEN
        RAISE EXCEPTION 'Double entry bookkeeping violation: debits must equal credits';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER double_entry_check 
    AFTER INSERT OR UPDATE ON journal_entries
    FOR EACH ROW EXECUTE FUNCTION check_double_entry();

-- Insert default admin user
INSERT INTO users (username, email, password_hash, role, created_at) 
VALUES ('admin', 'admin@fai-accountant.com', 
        crypt('admin123', gen_salt('bf')), 'admin', NOW())
ON CONFLICT (username) DO NOTHING;

-- Insert default chart of accounts
INSERT INTO chart_of_accounts (account_code, account_name, account_type, parent_account) VALUES
('1000', 'Assets', 'asset', NULL),
('1100', 'Current Assets', 'asset', '1000'),
('1110', 'Cash and Cash Equivalents', 'asset', '1100'),
('1120', 'Accounts Receivable', 'asset', '1100'),
('1130', 'Inventory', 'asset', '1100'),
('1200', 'Non-Current Assets', 'asset', '1000'),
('1210', 'Property, Plant & Equipment', 'asset', '1200'),
('2000', 'Liabilities', 'liability', NULL),
('2100', 'Current Liabilities', 'liability', '2000'),
('2110', 'Accounts Payable', 'liability', '2100'),
('2120', 'Short-term Debt', 'liability', '2100'),
('2200', 'Non-Current Liabilities', 'liability', '2000'),
('2210', 'Long-term Debt', 'liability', '2200'),
('3000', 'Equity', 'equity', NULL),
('3100', 'Share Capital', 'equity', '3000'),
('3200', 'Retained Earnings', 'equity', '3000'),
('4000', 'Revenue', 'revenue', NULL),
('4100', 'Sales Revenue', 'revenue', '4000'),
('4200', 'Service Revenue', 'revenue', '4000'),
('5000', 'Expenses', 'expense', NULL),
('5100', 'Cost of Goods Sold', 'expense', '5000'),
('5200', 'Operating Expenses', 'expense', '5000'),
('5210', 'Salaries and Wages', 'expense', '5200'),
('5220', 'Rent Expense', 'expense', '5200'),
('5230', 'Utilities Expense', 'expense', '5200'),
('5240', 'Professional Fees', 'expense', '5200')
ON CONFLICT (account_code) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fai_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO fai_user;

-- Create backup procedure
CREATE OR REPLACE FUNCTION create_backup(backup_name TEXT DEFAULT NULL)
RETURNS TEXT AS $$
DECLARE
    backup_file TEXT;
BEGIN
    IF backup_name IS NULL THEN
        backup_file := 'fai_backup_' || to_char(now(), 'YYYY_MM_DD_HH24_MI_SS');
    ELSE
        backup_file := backup_name;
    END IF;
    
    -- This would typically call pg_dump in a real environment
    -- For now, we'll just log the backup creation
    INSERT INTO audit_log (action, details, timestamp)
    VALUES ('database_backup', 'Backup created: ' || backup_file, NOW());
    
    RETURN backup_file;
END;
$$ LANGUAGE plpgsql;

COMMIT;