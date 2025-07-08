"""
Advanced User Permissions and Management Models
Implements modular permissions matrix with fine-grained access control
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app import db

class Permission(db.Model):
    """Core permissions system with 11 standard permission types"""
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)  # P1-P11
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_permissions = relationship("UserPermission", back_populates="permission")
    
    @staticmethod
    def get_default_permissions():
        """Get the standard 11 permission types"""
        return [
            {'code': 'P1', 'name': 'Create', 'description': 'Create new records'},
            {'code': 'P2', 'name': 'Edit', 'description': 'Edit existing records'},
            {'code': 'P3', 'name': 'Delete', 'description': 'Delete records'},
            {'code': 'P4', 'name': 'Update', 'description': 'Update record status'},
            {'code': 'P5', 'name': 'Draft', 'description': 'Create and save drafts'},
            {'code': 'P6', 'name': 'View', 'description': 'View records and data'},
            {'code': 'P7', 'name': 'Download', 'description': 'Download files and reports'},
            {'code': 'P8', 'name': 'Upload', 'description': 'Upload files and data'},
            {'code': 'P9', 'name': 'Email', 'description': 'Send emails and notifications'},
            {'code': 'P10', 'name': 'Approve', 'description': 'Approve transactions and workflows'},
            {'code': 'P11', 'name': 'Assign', 'description': 'Assign tasks and responsibilities'}
        ]

class Module(db.Model):
    """Software modules/segments for permission assignment"""
    __tablename__ = 'modules'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    parent_module_id = Column(Integer, ForeignKey('modules.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent_module = relationship("Module", remote_side=[id], backref="sub_modules")
    user_permissions = relationship("UserPermission", back_populates="module")
    
    @staticmethod
    def get_default_modules():
        """Get the standard software modules"""
        return [
            {'code': 'DASHBOARD', 'name': 'Dashboard', 'description': 'Main dashboard and overview'},
            {'code': 'ADMIN', 'name': 'Admin Portal', 'description': 'Administrative functions'},
            {'code': 'INVOICE', 'name': 'Invoice Portal', 'description': 'Invoice management'},
            {'code': 'INVENTORY', 'name': 'Inventory Portal', 'description': 'Inventory tracking'},
            {'code': 'GST', 'name': 'GST Portal', 'description': 'Tax compliance and GST'},
            {'code': 'AUDIT', 'name': 'Audit Portal', 'description': 'Audit trail and compliance'},
            {'code': 'REPORTS', 'name': 'Reports Portal', 'description': 'Financial reporting'},
            {'code': 'AI_INSIGHTS', 'name': 'AI Insights Portal', 'description': 'AI-powered analytics'},
            {'code': 'USERS', 'name': 'User Management', 'description': 'User and permissions management'},
            {'code': 'SETTINGS', 'name': 'System Settings', 'description': 'System configuration'},
            {'code': 'FILES', 'name': 'File Management', 'description': 'File upload and processing'}
        ]

class UserPermission(db.Model):
    """Junction table for user-module-permission assignments"""
    __tablename__ = 'user_permissions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False)
    is_granted = Column(Boolean, default=True)
    granted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="user_permissions")
    module = relationship("Module", back_populates="user_permissions")
    permission = relationship("Permission", back_populates="user_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'module_id', 'permission_id', name='uq_user_module_permission'),
        Index('idx_user_permissions_lookup', 'user_id', 'module_id', 'permission_id'),
        Index('idx_user_permissions_active', 'user_id', 'is_granted')
    )
    
    @classmethod
    def has_permission(cls, user_id, module_code, permission_code):
        """Check if user has specific permission for module"""
        from models import User
        
        return db.session.query(cls).join(
            Module, cls.module_id == Module.id
        ).join(
            Permission, cls.permission_id == Permission.id
        ).filter(
            cls.user_id == user_id,
            Module.code == module_code,
            Permission.code == permission_code,
            cls.is_granted == True,
            Module.is_active == True,
            Permission.is_active == True,
            (cls.expires_at.is_(None) | (cls.expires_at > datetime.utcnow()))
        ).first() is not None

class UserProfile(db.Model):
    """Extended user profile with KYC and contact information"""
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Primary contact methods
    primary_email = Column(String(120), nullable=True, index=True)
    secondary_email = Column(String(120), nullable=True)
    primary_phone = Column(String(20), nullable=True, index=True)
    secondary_phone = Column(String(20), nullable=True)
    
    # KYC Information
    kyc_status = Column(String(20), default='pending')  # pending, verified, rejected, expired
    kyc_document_type = Column(String(50), nullable=True)  # passport, driving_license, national_id
    kyc_document_number = Column(String(100), nullable=True)
    kyc_document_path = Column(String(500), nullable=True)
    kyc_verified_at = Column(DateTime, nullable=True)
    kyc_verified_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    kyc_expiry_date = Column(DateTime, nullable=True)
    kyc_notes = Column(Text, nullable=True)
    
    # Address Information
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Profile metadata
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    notification_preferences = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="profile")
    kyc_verified_by_user = relationship("User", foreign_keys=[kyc_verified_by])
    
    def is_kyc_required(self):
        """Check if KYC verification is required"""
        # This can be configured based on business rules
        return self.user.category in ['NON_INDIVIDUAL', 'PROFESSIONAL']
    
    def is_kyc_valid(self):
        """Check if KYC is valid and not expired"""
        if self.kyc_status != 'verified':
            return False
        if self.kyc_expiry_date and self.kyc_expiry_date < datetime.utcnow():
            return False
        return True

class PermissionAuditLog(db.Model):
    """Audit trail for permission changes"""
    __tablename__ = 'permission_audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    target_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False)
    action = Column(String(20), nullable=False)  # granted, revoked, modified
    old_value = Column(Boolean, nullable=True)
    new_value = Column(Boolean, nullable=True)
    reason = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    module = relationship("Module")
    permission = relationship("Permission")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user_target', 'user_id', 'target_user_id'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_action', 'action')
    )

class UserInvitation(db.Model):
    """Track user invitations and onboarding"""
    __tablename__ = 'user_invitations'
    
    id = Column(Integer, primary_key=True)
    invited_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    email = Column(String(120), nullable=True)
    phone = Column(String(20), nullable=True)
    invitation_code = Column(String(50), unique=True, nullable=False)
    intended_role = Column(String(50), nullable=True)
    intended_permissions = Column(Text, nullable=True)  # JSON string
    message = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String(20), default='sent')  # sent, accepted, expired, cancelled
    sent_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    # User creation tracking
    created_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    invited_by_user = relationship("User", foreign_keys=[invited_by])
    created_user = relationship("User", foreign_keys=[created_user_id])
    
    def is_expired(self):
        """Check if invitation has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if invitation is valid for acceptance"""
        return self.status == 'sent' and not self.is_expired()