
-- File Storage Metadata Schema
-- Stores metadata for files uploaded to GCP Object Storage

CREATE TABLE IF NOT EXISTS file_storage_metadata (
    id SERIAL PRIMARY KEY,
    
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
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Classification and categorization
    file_category VARCHAR(50) NOT NULL DEFAULT 'other',
    file_type VARCHAR(50), -- invoice, receipt, bank_statement, report, template
    document_classification JSONB, -- AI-based classification results
    
    -- Storage and access
    storage_bucket VARCHAR(200) NOT NULL DEFAULT 'fai-accountant-storage',
    storage_region VARCHAR(50) DEFAULT 'us-central1',
    signed_url_expires_at TIMESTAMP,
    
    -- Version control
    version INTEGER NOT NULL DEFAULT 1,
    is_current_version BOOLEAN DEFAULT TRUE,
    parent_file_id INTEGER REFERENCES file_storage_metadata(id),
    
    -- Timestamps
    upload_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP,
    last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Security and compliance
    encryption_key_id VARCHAR(200),
    is_encrypted BOOLEAN DEFAULT TRUE,
    retention_until TIMESTAMP,
    compliance_flags JSONB, -- GDPR, HIPAA, SOC2 compliance flags
    
    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'uploaded', -- uploaded, processing, processed, error
    processing_results JSONB,
    ocr_extracted_text TEXT,
    
    -- Access control
    access_level VARCHAR(50) DEFAULT 'private', -- private, shared, public
    shared_with JSONB, -- Array of user IDs who have access
    
    -- Audit and monitoring
    download_count INTEGER DEFAULT 0,
    last_downloaded_by INTEGER REFERENCES users(id),
    last_downloaded_at TIMESTAMP,
    
    -- Deletion and archival
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id),
    archive_status VARCHAR(50) DEFAULT 'active', -- active, archived, deleted
    
    -- Additional metadata
    tags JSONB, -- User-defined tags
    notes TEXT,
    business_metadata JSONB -- Business-specific metadata
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_file_storage_user_id ON file_storage_metadata(user_id);
CREATE INDEX IF NOT EXISTS idx_file_storage_organization_id ON file_storage_metadata(organization_id);
CREATE INDEX IF NOT EXISTS idx_file_storage_category ON file_storage_metadata(file_category);
CREATE INDEX IF NOT EXISTS idx_file_storage_type ON file_storage_metadata(file_type);
CREATE INDEX IF NOT EXISTS idx_file_storage_upload_date ON file_storage_metadata(upload_timestamp);
CREATE INDEX IF NOT EXISTS idx_file_storage_file_path ON file_storage_metadata(file_path);
CREATE INDEX IF NOT EXISTS idx_file_storage_hash ON file_storage_metadata(file_hash);
CREATE INDEX IF NOT EXISTS idx_file_storage_processing_status ON file_storage_metadata(processing_status);
CREATE INDEX IF NOT EXISTS idx_file_storage_is_deleted ON file_storage_metadata(is_deleted);

-- File access audit log
CREATE TABLE IF NOT EXISTS file_access_audit (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES file_storage_metadata(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Access details
    operation VARCHAR(50) NOT NULL, -- upload, download, delete, view, share
    access_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
    access_context JSONB -- Additional context data
);

-- Indexes for audit log
CREATE INDEX IF NOT EXISTS idx_file_access_audit_file_id ON file_access_audit(file_id);
CREATE INDEX IF NOT EXISTS idx_file_access_audit_user_id ON file_access_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_file_access_audit_timestamp ON file_access_audit(access_timestamp);
CREATE INDEX IF NOT EXISTS idx_file_access_audit_operation ON file_access_audit(operation);

-- File sharing permissions
CREATE TABLE IF NOT EXISTS file_sharing_permissions (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES file_storage_metadata(id) ON DELETE CASCADE,
    shared_by_user_id INTEGER NOT NULL REFERENCES users(id),
    shared_with_user_id INTEGER REFERENCES users(id),
    shared_with_organization_id INTEGER REFERENCES companies(id),
    
    -- Permission details
    permission_level VARCHAR(50) NOT NULL DEFAULT 'read', -- read, write, delete, admin
    can_download BOOLEAN DEFAULT TRUE,
    can_share BOOLEAN DEFAULT FALSE,
    can_edit_metadata BOOLEAN DEFAULT FALSE,
    
    -- Expiration
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT file_sharing_check CHECK (
        (shared_with_user_id IS NOT NULL AND shared_with_organization_id IS NULL) OR
        (shared_with_user_id IS NULL AND shared_with_organization_id IS NOT NULL)
    )
);

-- Indexes for sharing permissions
CREATE INDEX IF NOT EXISTS idx_file_sharing_file_id ON file_sharing_permissions(file_id);
CREATE INDEX IF NOT EXISTS idx_file_sharing_shared_with_user ON file_sharing_permissions(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_file_sharing_shared_with_org ON file_sharing_permissions(shared_with_organization_id);

-- File processing queue
CREATE TABLE IF NOT EXISTS file_processing_queue (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES file_storage_metadata(id) ON DELETE CASCADE,
    
    -- Processing details
    processing_type VARCHAR(100) NOT NULL, -- ocr, classification, validation, report_generation
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    
    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT,
    
    -- Timestamps
    queued_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Processing configuration
    processing_config JSONB,
    processing_results JSONB
);

-- Indexes for processing queue
CREATE INDEX IF NOT EXISTS idx_file_processing_queue_status ON file_processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_file_processing_queue_priority ON file_processing_queue(priority);
CREATE INDEX IF NOT EXISTS idx_file_processing_queue_queued_at ON file_processing_queue(queued_at);

-- Update trigger for last_modified_at
CREATE OR REPLACE FUNCTION update_last_modified_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_modified_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_file_storage_metadata_last_modified
    BEFORE UPDATE ON file_storage_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified_at();
