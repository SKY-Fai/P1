"""
Advanced Permissions Management Service
Handles user permissions, KYC verification, and user onboarding
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import uuid
import json
import logging
from flask import request
from sqlalchemy import and_, or_, func
from app import db
from models import User, UserCategory, UserRole, NonIndividualType, ProfessionalType
from permissions_models import (
    Permission, Module, UserPermission, UserProfile, 
    PermissionAuditLog, UserInvitation
)

class PermissionsManager:
    """Comprehensive permissions management system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def initialize_default_data(self):
        """Initialize default permissions and modules"""
        try:
            # Create default permissions
            permissions = Permission.get_default_permissions()
            for perm_data in permissions:
                existing = Permission.query.filter_by(code=perm_data['code']).first()
                if not existing:
                    permission = Permission(
                        code=perm_data['code'],
                        name=perm_data['name'],
                        description=perm_data['description']
                    )
                    db.session.add(permission)
            
            # Create default modules
            modules = Module.get_default_modules()
            for mod_data in modules:
                existing = Module.query.filter_by(code=mod_data['code']).first()
                if not existing:
                    module = Module(
                        code=mod_data['code'],
                        name=mod_data['name'],
                        description=mod_data['description']
                    )
                    db.session.add(module)
            
            db.session.commit()
            self.logger.info("Default permissions and modules initialized")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error initializing default data: {str(e)}")
            return False
    
    def create_user_with_permissions(self, user_data: Dict, permissions_matrix: Dict = None) -> Optional[User]:
        """Create user with specified permissions"""
        try:
            # Create user profile
            profile_data = user_data.get('profile', {})
            
            # Create basic user
            user = User(
                username=user_data.get('username', user_data.get('email', '')),
                email=user_data.get('email'),
                password_hash=user_data.get('password_hash'),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                category=user_data.get('category', UserCategory.INDIVIDUAL),
                role=user_data.get('role', UserRole.VIEWER),
                is_active=user_data.get('is_active', True),
                is_verified=user_data.get('is_verified', False)
            )
            
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create user profile
            profile = UserProfile(
                user_id=user.id,
                primary_email=profile_data.get('primary_email', user_data.get('email')),
                primary_phone=profile_data.get('primary_phone'),
                secondary_email=profile_data.get('secondary_email'),
                secondary_phone=profile_data.get('secondary_phone'),
                kyc_status=profile_data.get('kyc_status', 'pending'),
                timezone=profile_data.get('timezone', 'UTC'),
                language=profile_data.get('language', 'en')
            )
            
            db.session.add(profile)
            
            # Assign permissions if provided
            if permissions_matrix:
                self.assign_permissions_bulk(user.id, permissions_matrix, granted_by=None)
            else:
                # Assign default permissions based on role
                self.assign_default_permissions(user.id, user.role)
            
            db.session.commit()
            self.logger.info(f"User created successfully: {user.email}")
            return user
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating user: {str(e)}")
            return None
    
    def assign_default_permissions(self, user_id: int, role: UserRole, granted_by: int = None):
        """Assign default permissions based on user role"""
        try:
            # Define role-based permission templates
            role_permissions = {
                UserRole.ADMIN: {
                    'ADMIN': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11'],
                    'USERS': ['P1', 'P2', 'P3', 'P4', 'P6', 'P7', 'P10', 'P11'],
                    'SETTINGS': ['P1', 'P2', 'P4', 'P6', 'P7'],
                    'DASHBOARD': ['P6', 'P7'],
                    'REPORTS': ['P1', 'P6', 'P7', 'P8', 'P9'],
                    'FILES': ['P1', 'P2', 'P3', 'P6', 'P7', 'P8']
                },
                UserRole.MANAGER: {
                    'DASHBOARD': ['P6', 'P7'],
                    'INVOICE': ['P1', 'P2', 'P4', 'P5', 'P6', 'P7', 'P10'],
                    'INVENTORY': ['P1', 'P2', 'P4', 'P6', 'P7'],
                    'REPORTS': ['P6', 'P7', 'P9'],
                    'FILES': ['P6', 'P7', 'P8'],
                    'USERS': ['P6', 'P11']
                },
                UserRole.ACCOUNTANT: {
                    'DASHBOARD': ['P6', 'P7'],
                    'INVOICE': ['P1', 'P2', 'P4', 'P5', 'P6', 'P7'],
                    'GST': ['P1', 'P2', 'P4', 'P6', 'P7', 'P8'],
                    'REPORTS': ['P1', 'P6', 'P7', 'P8'],
                    'FILES': ['P6', 'P7', 'P8']
                },
                UserRole.EDITOR: {
                    'DASHBOARD': ['P6', 'P7'],
                    'INVOICE': ['P1', 'P2', 'P5', 'P6', 'P7'],
                    'INVENTORY': ['P1', 'P2', 'P6', 'P7'],
                    'FILES': ['P6', 'P7', 'P8']
                },
                UserRole.VIEWER: {
                    'DASHBOARD': ['P6'],
                    'REPORTS': ['P6', 'P7'],
                    'FILES': ['P6', 'P7']
                },
                UserRole.CA: {
                    'DASHBOARD': ['P6', 'P7'],
                    'ADMIN': ['P6', 'P10'],
                    'AUDIT': ['P1', 'P2', 'P4', 'P6', 'P7', 'P10'],
                    'REPORTS': ['P1', 'P6', 'P7', 'P8', 'P9'],
                    'GST': ['P1', 'P2', 'P4', 'P6', 'P7', 'P8', 'P10'],
                    'AI_INSIGHTS': ['P6', 'P7']
                },
                UserRole.AUDITOR: {
                    'DASHBOARD': ['P6', 'P7'],
                    'AUDIT': ['P1', 'P2', 'P4', 'P6', 'P7'],
                    'REPORTS': ['P6', 'P7', 'P8'],
                    'AI_INSIGHTS': ['P6']
                },
                UserRole.LEGAL: {
                    'DASHBOARD': ['P6', 'P7'],
                    'AUDIT': ['P6', 'P7'],
                    'REPORTS': ['P6', 'P7'],
                    'AI_INSIGHTS': ['P6']
                }
            }
            
            permissions_map = role_permissions.get(role, role_permissions[UserRole.VIEWER])
            self.assign_permissions_bulk(user_id, permissions_map, granted_by)
            
        except Exception as e:
            self.logger.error(f"Error assigning default permissions: {str(e)}")
            raise
    
    def assign_permissions_bulk(self, user_id: int, permissions_matrix: Dict, granted_by: int = None):
        """Assign multiple permissions at once"""
        try:
            for module_code, permission_codes in permissions_matrix.items():
                module = Module.query.filter_by(code=module_code).first()
                if not module:
                    continue
                
                for permission_code in permission_codes:
                    permission = Permission.query.filter_by(code=permission_code).first()
                    if not permission:
                        continue
                    
                    # Check if permission already exists
                    existing = UserPermission.query.filter_by(
                        user_id=user_id,
                        module_id=module.id,
                        permission_id=permission.id
                    ).first()
                    
                    if not existing:
                        user_permission = UserPermission(
                            user_id=user_id,
                            module_id=module.id,
                            permission_id=permission.id,
                            is_granted=True,
                            granted_by=granted_by
                        )
                        db.session.add(user_permission)
                        
                        # Log the assignment
                        self.log_permission_change(
                            user_id=granted_by or user_id,
                            target_user_id=user_id,
                            module_id=module.id,
                            permission_id=permission.id,
                            action='granted',
                            new_value=True
                        )
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error assigning permissions: {str(e)}")
            raise
    
    def revoke_permission(self, user_id: int, module_code: str, permission_code: str, revoked_by: int = None, reason: str = None):
        """Revoke specific permission from user"""
        try:
            module = Module.query.filter_by(code=module_code).first()
            permission = Permission.query.filter_by(code=permission_code).first()
            
            if not module or not permission:
                return False
            
            user_permission = UserPermission.query.filter_by(
                user_id=user_id,
                module_id=module.id,
                permission_id=permission.id
            ).first()
            
            if user_permission:
                old_value = user_permission.is_granted
                user_permission.is_granted = False
                
                # Log the change
                self.log_permission_change(
                    user_id=revoked_by or user_id,
                    target_user_id=user_id,
                    module_id=module.id,
                    permission_id=permission.id,
                    action='revoked',
                    old_value=old_value,
                    new_value=False,
                    reason=reason
                )
                
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error revoking permission: {str(e)}")
            return False
    
    def check_permission(self, user_id: int, module_code: str, permission_code: str) -> bool:
        """Check if user has specific permission"""
        return UserPermission.has_permission(user_id, module_code, permission_code)
    
    def get_user_permissions_matrix(self, user_id: int) -> Dict:
        """Get user's complete permissions matrix"""
        try:
            permissions = db.session.query(
                Module.code.label('module_code'),
                Module.name.label('module_name'),
                Permission.code.label('permission_code'),
                Permission.name.label('permission_name'),
                UserPermission.is_granted,
                UserPermission.granted_at,
                UserPermission.expires_at
            ).join(
                UserPermission, Module.id == UserPermission.module_id
            ).join(
                Permission, Permission.id == UserPermission.permission_id
            ).filter(
                UserPermission.user_id == user_id,
                Module.is_active == True,
                Permission.is_active == True
            ).order_by(Module.name, Permission.code).all()
            
            # Group by module
            matrix = {}
            for perm in permissions:
                if perm.module_code not in matrix:
                    matrix[perm.module_code] = {
                        'module_name': perm.module_name,
                        'permissions': {}
                    }
                
                matrix[perm.module_code]['permissions'][perm.permission_code] = {
                    'name': perm.permission_name,
                    'granted': perm.is_granted,
                    'granted_at': perm.granted_at.isoformat() if perm.granted_at else None,
                    'expires_at': perm.expires_at.isoformat() if perm.expires_at else None
                }
            
            return matrix
            
        except Exception as e:
            self.logger.error(f"Error getting user permissions: {str(e)}")
            return {}
    
    def create_user_invitation(self, invited_by: int, email: str = None, phone: str = None, 
                             intended_role: str = None, permissions_matrix: Dict = None, 
                             message: str = None, expires_in_days: int = 7) -> Optional[UserInvitation]:
        """Create user invitation with intended permissions"""
        try:
            invitation_code = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            invitation = UserInvitation(
                invited_by=invited_by,
                email=email,
                phone=phone,
                invitation_code=invitation_code,
                intended_role=intended_role,
                intended_permissions=json.dumps(permissions_matrix) if permissions_matrix else None,
                message=message,
                expires_at=expires_at
            )
            
            db.session.add(invitation)
            db.session.commit()
            
            self.logger.info(f"User invitation created: {invitation_code}")
            return invitation
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating invitation: {str(e)}")
            return None
    
    def process_invitation_acceptance(self, invitation_code: str, user_data: Dict) -> Tuple[bool, str, Optional[User]]:
        """Process invitation acceptance and create user"""
        try:
            invitation = UserInvitation.query.filter_by(invitation_code=invitation_code).first()
            
            if not invitation:
                return False, "Invalid invitation code", None
            
            if not invitation.is_valid():
                return False, "Invitation has expired or is no longer valid", None
            
            # Create user with intended permissions
            permissions_matrix = None
            if invitation.intended_permissions:
                permissions_matrix = json.loads(invitation.intended_permissions)
            
            user_data['role'] = invitation.intended_role or UserRole.VIEWER
            user = self.create_user_with_permissions(user_data, permissions_matrix)
            
            if user:
                # Update invitation status
                invitation.status = 'accepted'
                invitation.accepted_at = datetime.utcnow()
                invitation.created_user_id = user.id
                
                db.session.commit()
                
                return True, "User created successfully", user
            else:
                return False, "Failed to create user", None
                
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error processing invitation: {str(e)}")
            return False, str(e), None
    
    def verify_kyc(self, user_id: int, document_type: str, document_number: str, 
                   document_path: str, verified_by: int, notes: str = None) -> bool:
        """Verify user KYC"""
        try:
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                return False
            
            profile.kyc_status = 'verified'
            profile.kyc_document_type = document_type
            profile.kyc_document_number = document_number
            profile.kyc_document_path = document_path
            profile.kyc_verified_at = datetime.utcnow()
            profile.kyc_verified_by = verified_by
            profile.kyc_notes = notes
            
            # Set expiry based on document type
            if document_type == 'passport':
                profile.kyc_expiry_date = datetime.utcnow() + timedelta(days=3650)  # 10 years
            else:
                profile.kyc_expiry_date = datetime.utcnow() + timedelta(days=1825)  # 5 years
            
            db.session.commit()
            self.logger.info(f"KYC verified for user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error verifying KYC: {str(e)}")
            return False
    
    def log_permission_change(self, user_id: int, target_user_id: int, module_id: int, 
                            permission_id: int, action: str, old_value: bool = None, 
                            new_value: bool = None, reason: str = None):
        """Log permission changes for audit trail"""
        try:
            audit_log = PermissionAuditLog(
                user_id=user_id,
                target_user_id=target_user_id,
                module_id=module_id,
                permission_id=permission_id,
                action=action,
                old_value=old_value,
                new_value=new_value,
                reason=reason,
                ip_address=request.remote_addr if request else None,
                user_agent=request.user_agent.string if request and request.user_agent else None
            )
            
            db.session.add(audit_log)
            
        except Exception as e:
            self.logger.error(f"Error logging permission change: {str(e)}")
    
    def get_permissions_audit_trail(self, user_id: int = None, days: int = 30) -> List[Dict]:
        """Get permissions audit trail"""
        try:
            # Use aliases to avoid duplicate table names
            from sqlalchemy.orm import aliased
            actor_user = aliased(User)
            target_user = aliased(User)
            
            query = db.session.query(
                PermissionAuditLog,
                actor_user.username.label('actor_username'),
                actor_user.email.label('actor_email'),
                target_user.username.label('target_username'),
                target_user.email.label('target_email'),
                Module.name.label('module_name'),
                Permission.name.label('permission_name')
            ).join(
                actor_user, PermissionAuditLog.user_id == actor_user.id, isouter=True
            ).join(
                target_user, PermissionAuditLog.target_user_id == target_user.id, isouter=True
            ).join(
                Module, PermissionAuditLog.module_id == Module.id
            ).join(
                Permission, PermissionAuditLog.permission_id == Permission.id
            )
            
            if user_id:
                query = query.filter(
                    or_(
                        PermissionAuditLog.user_id == user_id,
                        PermissionAuditLog.target_user_id == user_id
                    )
                )
            
            if days:
                since_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(PermissionAuditLog.timestamp >= since_date)
            
            results = query.order_by(PermissionAuditLog.timestamp.desc()).all()
            
            audit_trail = []
            for result in results:
                log = result[0]
                audit_trail.append({
                    'id': log.id,
                    'actor': {
                        'username': result.actor_username,
                        'email': result.actor_email
                    },
                    'target': {
                        'username': result.target_username,
                        'email': result.target_email
                    },
                    'module': result.module_name,
                    'permission': result.permission_name,
                    'action': log.action,
                    'old_value': log.old_value,
                    'new_value': log.new_value,
                    'reason': log.reason,
                    'timestamp': log.timestamp.isoformat(),
                    'ip_address': log.ip_address
                })
            
            return audit_trail
            
        except Exception as e:
            self.logger.error(f"Error getting audit trail: {str(e)}")
            return []