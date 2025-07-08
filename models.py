from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app import db
import enum

class UserCategory(enum.Enum):
    INDIVIDUAL = "individual"
    NON_INDIVIDUAL = "non_individual"
    PROFESSIONAL = "professional"

class NonIndividualType(enum.Enum):
    COMPANY = "company"
    LLP = "llp"

class ProfessionalType(enum.Enum):
    CA = "ca"
    CS = "cs"
    LEGAL = "legal"

class UserRole(enum.Enum):
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    AUDITOR = "auditor"
    CA = "ca"
    CLIENT_SUCCESS = "client_success"
    LEGAL = "legal"
    VIEWER = "viewer"
    EDITOR = "editor"
    MANAGER = "manager"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    
    # Hierarchical User Structure
    category = Column(Enum(UserCategory), nullable=False)
    non_individual_type = Column(Enum(NonIndividualType), nullable=True)
    professional_type = Column(Enum(ProfessionalType), nullable=True)
    
    # Parent-Child Relationship for hierarchical structure
    parent_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    parent_user = relationship("User", remote_side=[id], backref="sub_users")
    
    # Administrative control
    is_admin = Column(Boolean, default=False)  # Primary admin of the account
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Professional Services Code System
    user_code = Column(String(20), unique=True, nullable=True)  # e.g., CA01CL01, CS01CM01
    access_code = Column(String(10), nullable=True)  # e.g., 5678, 8723
    login_link = Column(String(200), nullable=True)  # e.g., f-ai.in/CA01CL01
    base_user_code = Column(String(10), nullable=True)  # e.g., CA01, CS01
    
    # Relationships
    uploaded_files = relationship("UploadedFile", back_populates="user")
    journal_entries = relationship("JournalEntry", back_populates="created_by_user", foreign_keys="JournalEntry.created_by")
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role):
        if isinstance(role, str):
            return self.role.value == role
        return self.role == role

    def is_main_admin(self):
        """Check if user is the main admin (first user in hierarchy)"""
        return self.parent_user_id is None and self.is_admin

    def is_sub_user(self):
        """Check if user is a sub-user"""
        return self.parent_user_id is not None

    def get_main_admin(self):
        """Get the main admin user in the hierarchy"""
        if self.is_main_admin():
            return self
        current = self
        while current.parent_user:
            current = current.parent_user
            if current.is_main_admin():
                return current
        return None

    def get_accessible_companies(self):
        """Get list of companies this user can access"""
        access_records = UserCompanyAccess.query.filter_by(user_id=self.id, is_active=True).all()
        return [access.company for access in access_records]

    def can_access_company(self, company_id):
        """Check if user can access specific company"""
        access = UserCompanyAccess.query.filter_by(
            user_id=self.id, 
            company_id=company_id, 
            is_active=True
        ).first()
        return access is not None

    def can_access_portal(self, portal_name):
        """Check if user can access specific portal based on role and category"""
        portal_permissions = {
            'admin': ['admin', 'invoice', 'inventory', 'gst', 'audit', 'reports', 'ai_insights'],
            'accountant': ['invoice', 'inventory', 'reports', 'ai_insights'],
            'auditor': ['audit', 'reports'],
            'ca': ['admin', 'invoice', 'inventory', 'gst', 'audit', 'reports', 'ai_insights'],
            'cs': ['admin', 'audit', 'reports', 'ai_insights'],
            'legal': ['audit', 'reports', 'ai_insights'],
            'manager': ['invoice', 'inventory', 'reports', 'ai_insights'],
            'editor': ['invoice', 'inventory', 'reports'],
            'viewer': ['reports']
        }
        
        # Main admins can access everything
        if self.is_main_admin():
            return True
            
        user_portals = portal_permissions.get(self.role.value, [])
        return portal_name in user_portals

    def can_create_sub_users(self):
        """Check if user can create sub-users"""
        return self.is_main_admin() or self.role in [UserRole.ADMIN, UserRole.MANAGER]

    def get_category_display(self):
        """Get display name for user category"""
        if self.category == UserCategory.INDIVIDUAL:
            return "Individual"
        elif self.category == UserCategory.NON_INDIVIDUAL:
            return f"{self.non_individual_type.value.upper()}" if self.non_individual_type else "Non-Individual"
        elif self.category == UserCategory.PROFESSIONAL:
            return f"Professional ({self.professional_type.value.upper()})" if self.professional_type else "Professional"
        return "Unknown"

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    registration_number = Column(String(100), unique=True)
    tax_id = Column(String(100), unique=True)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(120))
    
    # Financial configuration
    financial_year_start = Column(String(10))  # Format: MM-DD
    base_currency = Column(String(3), default='USD')
    
    # Ownership and access
    owner_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner_user = relationship("User", foreign_keys=[owner_user_id])
    
    # Company categorization
    company_type = Column(Enum(NonIndividualType), nullable=True)  # COMPANY or LLP
    industry = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chart_of_accounts = relationship("ChartOfAccount", back_populates="company")
    journal_entries = relationship("JournalEntry", back_populates="company")
    user_access = relationship("UserCompanyAccess", back_populates="company")

class UserCompanyAccess(db.Model):
    """Manages user access to different companies with role-based permissions"""
    __tablename__ = 'user_company_access'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    
    # Access control
    access_level = Column(String(50), nullable=False)  # 'full', 'read_write', 'read_only', 'restricted'
    can_view_reports = Column(Boolean, default=True)
    can_edit_transactions = Column(Boolean, default=False)
    can_manage_settings = Column(Boolean, default=False)
    can_export_data = Column(Boolean, default=True)
    
    # Professional access (for CA, CS, Legal professionals)
    is_professional_access = Column(Boolean, default=False)
    professional_permissions = Column(Text, nullable=True)  # JSON string for detailed permissions
    
    # Status and timestamps
    is_active = Column(Boolean, default=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    company = relationship("Company", back_populates="user_access")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    # Unique constraint to prevent duplicate access records
    __table_args__ = (db.UniqueConstraint('user_id', 'company_id'),)

class ChartOfAccount(db.Model):
    __tablename__ = 'chart_of_accounts'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    account_code = Column(String(20), nullable=False)
    account_name = Column(String(200), nullable=False)
    account_type = Column(String(50), nullable=False)  # Assets, Liabilities, Equity, Revenue, Expenses
    parent_account_id = Column(Integer, ForeignKey('chart_of_accounts.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="chart_of_accounts")
    parent_account = relationship("ChartOfAccount", remote_side=[id])
    journal_entries = relationship("JournalEntry", back_populates="account")

class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)  # excel, csv
    status = Column(String(50), default='uploaded')  # uploaded, processing, validated, processed, error
    validation_errors = Column(Text)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="uploaded_files")
    processing_results = relationship("ProcessingResult", back_populates="uploaded_file")

class ProcessingResult(db.Model):
    __tablename__ = 'processing_results'
    
    id = Column(Integer, primary_key=True)
    uploaded_file_id = Column(Integer, ForeignKey('uploaded_files.id'), nullable=False)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    error_records = Column(Integer, default=0)
    processing_log = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    uploaded_file = relationship("UploadedFile", back_populates="processing_results")

class JournalEntryStatus(enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('chart_of_accounts.id'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    entry_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    reference_number = Column(String(100))
    debit_amount = Column(Float, default=0.0)
    credit_amount = Column(Float, default=0.0)
    currency = Column(String(3), default='USD')
    is_posted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Enhanced workflow fields
    status = Column(Enum(JournalEntryStatus), default=JournalEntryStatus.DRAFT)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Source tracking
    source_type = Column(String(50), default='manual')  # manual, automated, import
    source_reference = Column(String(200), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="journal_entries")
    account = relationship("ChartOfAccount", back_populates="journal_entries")
    created_by_user = relationship("User", back_populates="journal_entries", foreign_keys=[created_by])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    rejected_by_user = relationship("User", foreign_keys=[rejected_by])

class ManualJournalHeader(db.Model):
    __tablename__ = 'manual_journal_headers'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    journal_number = Column(String(50), unique=True, nullable=False)
    entry_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    reference_number = Column(String(100))
    
    # Status and workflow
    status = Column(Enum(JournalEntryStatus), default=JournalEntryStatus.DRAFT)
    total_debits = Column(Float, default=0.0)
    total_credits = Column(Float, default=0.0)
    
    # Workflow tracking
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    posted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    
    rejected_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Attachments and notes
    notes = Column(Text, nullable=True)
    attachments = Column(Text, nullable=True)  # JSON array of file paths
    
    # Relationships
    company = relationship("Company")
    created_by_user = relationship("User", foreign_keys=[created_by])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    posted_by_user = relationship("User", foreign_keys=[posted_by])
    rejected_by_user = relationship("User", foreign_keys=[rejected_by])
    journal_lines = relationship("ManualJournalLine", back_populates="journal_header", cascade="all, delete-orphan")

class ManualJournalLine(db.Model):
    __tablename__ = 'manual_journal_lines'
    
    id = Column(Integer, primary_key=True)
    journal_header_id = Column(Integer, ForeignKey('manual_journal_headers.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('chart_of_accounts.id'), nullable=False)
    line_description = Column(Text, nullable=False)
    debit_amount = Column(Float, default=0.0)
    credit_amount = Column(Float, default=0.0)
    line_number = Column(Integer, nullable=False)
    
    # Additional line details
    tax_code = Column(String(20), nullable=True)
    cost_center = Column(String(50), nullable=True)
    project_code = Column(String(50), nullable=True)
    
    # Relationships
    journal_header = relationship("ManualJournalHeader", back_populates="journal_lines")
    account = relationship("ChartOfAccount")

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(100), unique=True, nullable=False)
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(120))
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    status = Column(String(50), default='draft')  # draft, sent, paid, overdue, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoice_items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    item_name = Column(String(200), nullable=False)
    description = Column(Text)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_items")

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    
    id = Column(Integer, primary_key=True)
    item_code = Column(String(100), unique=True, nullable=False)
    item_name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    unit_of_measure = Column(String(20))
    current_stock = Column(Float, default=0.0)
    reorder_level = Column(Float, default=0.0)
    unit_cost = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(100), nullable=False)
    table_name = Column(String(100))
    record_id = Column(Integer)
    old_values = Column(Text)
    new_values = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

class GSTRecord(db.Model):
    __tablename__ = 'gst_records'
    
    id = Column(Integer, primary_key=True)
    gstin = Column(String(20), nullable=False)
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(DateTime, nullable=False)
    taxable_amount = Column(Float, nullable=False)
    cgst_rate = Column(Float, default=0.0)
    cgst_amount = Column(Float, default=0.0)
    sgst_rate = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_rate = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    total_tax = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    return_period = Column(String(10))  # Format: MM-YYYY
    created_at = Column(DateTime, default=datetime.utcnow)

class FinancialReport(db.Model):
    __tablename__ = 'financial_reports'
    
    id = Column(Integer, primary_key=True)
    report_type = Column(String(100), nullable=False)  # balance_sheet, income_statement, cash_flow, etc.
    report_period = Column(String(20), nullable=False)  # Format: MM-YYYY or YYYY
    generated_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_path = Column(String(500))
    parameters = Column(Text)  # JSON string of report parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    generated_by_user = relationship("User")
