
-- F-AI Accountant Production Database Schema
-- PostgreSQL optimized for GCP deployment

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table with enhanced security
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    
    -- Hierarchical structure
    category VARCHAR(20) DEFAULT 'individual' CHECK (category IN ('individual', 'non_individual', 'professional')),
    non_individual_type VARCHAR(20) CHECK (non_individual_type IN ('company', 'llp')),
    professional_type VARCHAR(20) CHECK (professional_type IN ('ca', 'cs', 'legal')),
    
    -- Professional codes
    user_code VARCHAR(20) UNIQUE,
    access_code VARCHAR(10),
    login_link VARCHAR(200),
    base_user_code VARCHAR(10),
    parent_user_id INTEGER REFERENCES users(id),
    
    -- Access control
    role VARCHAR(20) DEFAULT 'viewer' CHECK (role IN ('admin', 'accountant', 'auditor', 'ca', 'cs', 'legal', 'manager', 'editor', 'viewer')),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    name VARCHAR(200) NOT NULL,
    registration_number VARCHAR(100) UNIQUE,
    tax_id VARCHAR(100) UNIQUE,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(120),
    website VARCHAR(200),
    
    -- Financial configuration
    financial_year_start VARCHAR(10), -- MM-DD format
    base_currency VARCHAR(3) DEFAULT 'USD',
    
    -- Ownership
    owner_user_id INTEGER NOT NULL REFERENCES users(id),
    company_type VARCHAR(20) CHECK (company_type IN ('company', 'llp')),
    industry VARCHAR(100),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User company access control
CREATE TABLE IF NOT EXISTS user_company_access (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    company_id INTEGER NOT NULL REFERENCES companies(id),
    
    -- Access control
    access_level VARCHAR(50) NOT NULL DEFAULT 'read_only',
    can_view_reports BOOLEAN DEFAULT TRUE,
    can_edit_transactions BOOLEAN DEFAULT FALSE,
    can_manage_settings BOOLEAN DEFAULT FALSE,
    can_export_data BOOLEAN DEFAULT TRUE,
    
    -- Professional access
    is_professional_access BOOLEAN DEFAULT FALSE,
    professional_permissions JSONB,
    
    -- Status and timestamps
    is_active BOOLEAN DEFAULT TRUE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(user_id, company_id)
);

-- File storage metadata for GCP Object Storage
CREATE TABLE IF NOT EXISTS file_storage_metadata (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    
    -- File identification
    file_path VARCHAR(1000) NOT NULL UNIQUE,
    original_filename VARCHAR(500) NOT NULL,
    secure_filename VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    
    -- File properties
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(200),
    content_type VARCHAR(200),
    file_extension VARCHAR(10),
    
    -- Ownership and organization
    user_id INTEGER NOT NULL REFERENCES users(id),
    organization_id INTEGER REFERENCES companies(id),
    
    -- Classification
    file_category VARCHAR(50) NOT NULL DEFAULT 'other',
    file_type VARCHAR(50),
    document_classification JSONB,
    
    -- Storage details
    storage_bucket VARCHAR(200) NOT NULL DEFAULT 'fai-accountant-storage',
    storage_region VARCHAR(50) DEFAULT 'us-central1',
    signed_url_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Version control
    version INTEGER NOT NULL DEFAULT 1,
    is_current_version BOOLEAN DEFAULT TRUE,
    parent_file_id INTEGER REFERENCES file_storage_metadata(id),
    
    -- Timestamps
    upload_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    last_modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Security and compliance
    encryption_key_id VARCHAR(200),
    is_encrypted BOOLEAN DEFAULT TRUE,
    retention_until TIMESTAMP WITH TIME ZONE,
    compliance_flags JSONB,
    
    -- Processing
    processing_status VARCHAR(50) DEFAULT 'uploaded',
    processing_results JSONB,
    ocr_extracted_text TEXT,
    
    -- Access control
    access_level VARCHAR(50) DEFAULT 'private',
    shared_with JSONB,
    
    -- Audit and monitoring
    download_count INTEGER DEFAULT 0,
    last_downloaded_by INTEGER REFERENCES users(id),
    last_downloaded_at TIMESTAMP WITH TIME ZONE,
    
    -- Deletion and archival
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by INTEGER REFERENCES users(id),
    archive_status VARCHAR(50) DEFAULT 'active',
    
    -- Additional metadata
    tags JSONB,
    notes TEXT,
    business_metadata JSONB
);

-- Chart of accounts
CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    account_code VARCHAR(20) NOT NULL,
    account_name VARCHAR(200) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
    parent_account_id INTEGER REFERENCES chart_of_accounts(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(company_id, account_code)
);

-- Journal entries with enhanced workflow
CREATE TABLE IF NOT EXISTS journal_entries (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    company_id INTEGER REFERENCES companies(id),
    account_id INTEGER REFERENCES chart_of_accounts(id),
    created_by INTEGER REFERENCES users(id),
    
    -- Entry details
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT NOT NULL,
    reference_number VARCHAR(100),
    debit_amount DECIMAL(15,2) DEFAULT 0.00,
    credit_amount DECIMAL(15,2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Status and workflow
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending_review', 'reviewed', 'approved', 'posted', 'rejected')),
    is_posted BOOLEAN DEFAULT FALSE,
    
    -- Workflow tracking
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_by INTEGER REFERENCES users(id),
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    notes TEXT,
    
    -- Source tracking
    source_type VARCHAR(50) DEFAULT 'manual',
    source_reference VARCHAR(200),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Manual journal headers for complex entries
CREATE TABLE IF NOT EXISTS manual_journal_headers (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    journal_number VARCHAR(50) UNIQUE NOT NULL,
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT NOT NULL,
    reference_number VARCHAR(100),
    
    -- Status and workflow
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending_review', 'reviewed', 'approved', 'posted', 'rejected')),
    total_debits DECIMAL(15,2) DEFAULT 0.00,
    total_credits DECIMAL(15,2) DEFAULT 0.00,
    
    -- Workflow tracking
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approval_notes TEXT,
    
    posted_by INTEGER REFERENCES users(id),
    posted_at TIMESTAMP WITH TIME ZONE,
    
    rejected_by INTEGER REFERENCES users(id),
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    
    -- Attachments and notes
    notes TEXT,
    attachments JSONB
);

-- Manual journal lines
CREATE TABLE IF NOT EXISTS manual_journal_lines (
    id SERIAL PRIMARY KEY,
    journal_header_id INTEGER NOT NULL REFERENCES manual_journal_headers(id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES chart_of_accounts(id),
    line_description TEXT NOT NULL,
    debit_amount DECIMAL(15,2) DEFAULT 0.00,
    credit_amount DECIMAL(15,2) DEFAULT 0.00,
    line_number INTEGER NOT NULL,
    
    -- Additional details
    tax_code VARCHAR(20),
    cost_center VARCHAR(50),
    project_code VARCHAR(50)
);

-- File access audit log
CREATE TABLE IF NOT EXISTS file_access_audit (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES file_storage_metadata(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    
    -- Access details
    operation VARCHAR(50) NOT NULL,
    access_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    
    -- Request details
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    response_status INTEGER,
    
    -- Success/failure
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Additional context
    session_id VARCHAR(100),
    api_endpoint VARCHAR(200),
    access_context JSONB
);

-- Comprehensive audit log
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
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_user_code ON users(user_code);
CREATE INDEX IF NOT EXISTS idx_users_category ON users(category);
CREATE INDEX IF NOT EXISTS idx_users_parent ON users(parent_user_id);

CREATE INDEX IF NOT EXISTS idx_companies_owner ON companies(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_companies_active ON companies(is_active);

CREATE INDEX IF NOT EXISTS idx_file_storage_user ON file_storage_metadata(user_id);
CREATE INDEX IF NOT EXISTS idx_file_storage_org ON file_storage_metadata(organization_id);
CREATE INDEX IF NOT EXISTS idx_file_storage_category ON file_storage_metadata(file_category);
CREATE INDEX IF NOT EXISTS idx_file_storage_upload_date ON file_storage_metadata(upload_timestamp);
CREATE INDEX IF NOT EXISTS idx_file_storage_hash ON file_storage_metadata(file_hash);
CREATE INDEX IF NOT EXISTS idx_file_storage_deleted ON file_storage_metadata(is_deleted);

CREATE INDEX IF NOT EXISTS idx_chart_company ON chart_of_accounts(company_id);
CREATE INDEX IF NOT EXISTS idx_chart_code ON chart_of_accounts(account_code);
CREATE INDEX IF NOT EXISTS idx_chart_type ON chart_of_accounts(account_type);

CREATE INDEX IF NOT EXISTS idx_journal_company ON journal_entries(company_id);
CREATE INDEX IF NOT EXISTS idx_journal_account ON journal_entries(account_id);
CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_status ON journal_entries(status);
CREATE INDEX IF NOT EXISTS idx_journal_created_by ON journal_entries(created_by);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);

CREATE INDEX IF NOT EXISTS idx_file_access_file ON file_access_audit(file_id);
CREATE INDEX IF NOT EXISTS idx_file_access_user ON file_access_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_file_access_timestamp ON file_access_audit(access_timestamp);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_file_storage_filename_search ON file_storage_metadata USING gin(original_filename gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_journal_description_search ON journal_entries USING gin(description gin_trgm_ops);

-- Update triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_manual_journal_headers_updated_at BEFORE UPDATE ON manual_journal_headers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) for multi-tenancy
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_storage_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY user_companies ON companies
    FOR ALL TO authenticated
    USING (owner_user_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY user_files ON file_storage_metadata
    FOR ALL TO authenticated
    USING (user_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY company_journal_entries ON journal_entries
    FOR ALL TO authenticated
    USING (company_id IN (
        SELECT id FROM companies WHERE owner_user_id = current_setting('app.current_user_id')::INTEGER
    ));
