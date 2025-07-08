"""
User Code Generator for Professional Services Login Structure
Generates unique codes, login links, and access codes for Base and Sub-users
"""

import random
import string
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func
from models import User, db

class UserCodeGenerator:
    """Generates and manages professional user codes and access links"""
    
    BASE_USER_CODES = {
        'CA': 'CA01',
        'CS': 'CS01', 
        'LAWYER': 'LW01',
        'CLIENT': 'CL01'
    }
    
    SUB_USER_PREFIXES = {
        'individual': 'CL',
        'company': 'CM',
        'llp': 'LLP',
        'ca': 'CA',
        'cs': 'CS',
        'lawyer': 'LW'
    }
    
    BASE_DOMAIN = 'f-ai.in'
    
    def __init__(self):
        self.used_codes = set()
        self.used_access_codes = set()
        
    def generate_base_user_code(self, user_type: str) -> str:
        """Generate base user code for CA, CS, Lawyer, or Client"""
        user_type_upper = user_type.upper()
        
        if user_type_upper in self.BASE_USER_CODES:
            return self.BASE_USER_CODES[user_type_upper]
        
        # For custom base users, generate sequential codes
        existing_codes = self._get_existing_base_codes(user_type_upper)
        next_number = len(existing_codes) + 1
        return f"{user_type_upper}{next_number:02d}"
    
    def generate_sub_user_code(self, base_code: str, sub_type: str, sub_category: str = None) -> str:
        """Generate sub-user code with base prefix"""
        prefix = self.SUB_USER_PREFIXES.get(sub_type.lower(), sub_type.upper())
        
        # Get existing sub-user codes for this base
        existing_subs = self._get_existing_sub_codes(base_code, prefix)
        next_number = len(existing_subs) + 1
        
        return f"{base_code}{prefix}{next_number:02d}"
    
    def generate_access_code(self, length: int = 4) -> str:
        """Generate unique 4-digit access code"""
        while True:
            code = ''.join(random.choices(string.digits, k=length))
            if code not in self.used_access_codes:
                self.used_access_codes.add(code)
                return code
    
    def generate_login_link(self, user_code: str) -> str:
        """Generate login link for user code"""
        return f"{self.BASE_DOMAIN}/{user_code}"
    
    def create_user_with_codes(self, base_type: str, sub_type: str, sub_category: str = None, 
                              user_data: Dict = None) -> Tuple[str, str, str]:
        """Create user with generated codes and return (user_code, login_link, access_code)"""
        
        # Generate base code if this is a new base user
        base_code = self.generate_base_user_code(base_type)
        
        # Generate sub-user code
        user_code = self.generate_sub_user_code(base_code, sub_type, sub_category)
        
        # Generate access code
        access_code = self.generate_access_code()
        
        # Generate login link
        login_link = self.generate_login_link(user_code)
        
        return user_code, login_link, access_code
    
    def get_user_hierarchy_structure(self) -> Dict:
        """Get complete user hierarchy structure as defined in the table"""
        return {
            'CA': {
                'base_code': 'CA01',
                'sub_users': [
                    {'category': 'Individual', 'type': 'Individual', 'code': 'CA01CL01', 'access_code': '5678'},
                    {'category': 'Non-Individual', 'type': 'Company', 'code': 'CA01CM01', 'access_code': '8723'},
                    {'category': 'Non-Individual', 'type': 'LLP', 'code': 'CA01LLP01', 'access_code': '2345'},
                    {'category': 'Professional', 'type': 'CA', 'code': 'CA01CA01', 'access_code': '3321'},
                    {'category': 'Professional', 'type': 'CS', 'code': 'CA01CS01', 'access_code': '7865'},
                    {'category': 'Professional', 'type': 'Lawyer', 'code': 'CA01LW01', 'access_code': '2190'},
                ]
            },
            'CS': {
                'base_code': 'CS01',
                'sub_users': [
                    {'category': 'Individual', 'type': 'Individual', 'code': 'CS01CL01', 'access_code': '4590'},
                    {'category': 'Non-Individual', 'type': 'Company', 'code': 'CS01CM01', 'access_code': '8751'},
                    {'category': 'Non-Individual', 'type': 'LLP', 'code': 'CS01LLP01', 'access_code': '9281'},
                    {'category': 'Professional', 'type': 'CA', 'code': 'CS01CA01', 'access_code': '1244'},
                    {'category': 'Professional', 'type': 'CS', 'code': 'CS01CS01', 'access_code': '6512'},
                    {'category': 'Professional', 'type': 'Lawyer', 'code': 'CS01LW01', 'access_code': '7782'},
                ]
            },
            'LAWYER': {
                'base_code': 'LW01',
                'sub_users': [
                    {'category': 'Individual', 'type': 'Individual', 'code': 'LW01CL01', 'access_code': '6712'},
                    {'category': 'Non-Individual', 'type': 'Company', 'code': 'LW01CM01', 'access_code': '8804'},
                    {'category': 'Non-Individual', 'type': 'LLP', 'code': 'LW01LLP01', 'access_code': '3300'},
                    {'category': 'Professional', 'type': 'CA', 'code': 'LW01CA01', 'access_code': '9222'},
                    {'category': 'Professional', 'type': 'CS', 'code': 'LW01CS01', 'access_code': '5583'},
                    {'category': 'Professional', 'type': 'Lawyer', 'code': 'LW01LW01', 'access_code': '4411'},
                ]
            },
            'CLIENT': {
                'base_code': 'CL01',
                'sub_users': [
                    {'category': 'Professional', 'type': 'CA', 'code': 'CL01CA01', 'access_code': '8901'},
                    {'category': 'Professional', 'type': 'CS', 'code': 'CL01CS01', 'access_code': '5580'},
                    {'category': 'Professional', 'type': 'Lawyer', 'code': 'CL01LW01', 'access_code': '3310'},
                    {'category': 'Individual', 'type': 'Individual', 'code': 'CL01CL01', 'access_code': '1001'},
                    {'category': 'Non-Individual', 'type': 'Company', 'code': 'CL01CM01', 'access_code': '2002'},
                    {'category': 'Non-Individual', 'type': 'LLP', 'code': 'CL01LLP01', 'access_code': '3003'},
                ]
            }
        }
    
    def _get_existing_base_codes(self, user_type: str) -> List[str]:
        """Get existing base codes for a user type"""
        with db.session() as session:
            users = session.query(User).filter(
                User.professional_type == user_type,
                User.parent_user_id.is_(None)
            ).all()
            return [user.username for user in users if user.username.startswith(user_type)]
    
    def _get_existing_sub_codes(self, base_code: str, prefix: str) -> List[str]:
        """Get existing sub-user codes for a base code and prefix"""
        with db.session() as session:
            pattern = f"{base_code}{prefix}%"
            users = session.query(User).filter(
                User.username.like(pattern)
            ).all()
            return [user.username for user in users]
    
    def get_user_permissions(self, user_code: str) -> Dict:
        """Get user permissions based on code structure"""
        permissions = {
            'can_view_reports': True,
            'can_edit_transactions': False,
            'can_manage_settings': False,
            'can_export_data': True,
            'portal_access': []
        }
        
        # Determine permissions based on user type
        if 'CA' in user_code:
            permissions.update({
                'can_edit_transactions': True,
                'can_manage_settings': True,
                'portal_access': ['admin', 'audit', 'reports', 'gst', 'ai_insights']
            })
        elif 'CS' in user_code:
            permissions.update({
                'can_edit_transactions': True,
                'portal_access': ['audit', 'reports', 'gst', 'ai_insights']
            })
        elif 'LW' in user_code:
            permissions.update({
                'portal_access': ['audit', 'reports', 'ai_insights']
            })
        elif 'CL' in user_code:
            permissions.update({
                'portal_access': ['reports', 'ai_insights']
            })
        elif 'CM' in user_code or 'LLP' in user_code:
            permissions.update({
                'can_edit_transactions': True,
                'portal_access': ['invoice', 'inventory', 'reports', 'gst']
            })
        
        return permissions
    
    def validate_access_code(self, user_code: str, access_code: str) -> bool:
        """Validate access code for a user"""
        hierarchy = self.get_user_hierarchy_structure()
        
        for base_type, data in hierarchy.items():
            for sub_user in data['sub_users']:
                if sub_user['code'] == user_code:
                    return sub_user['access_code'] == access_code
        
        return False
    
    def create_demo_users(self) -> Dict:
        """Create demo users for all code combinations"""
        hierarchy = self.get_user_hierarchy_structure()
        created_users = {}
        
        for base_type, data in hierarchy.items():
            base_code = data['base_code']
            created_users[base_type] = {
                'base_code': base_code,
                'sub_users': []
            }
            
            for sub_user in data['sub_users']:
                user_data = {
                    'username': sub_user['code'],
                    'user_code': sub_user['code'],
                    'access_code': sub_user['access_code'],
                    'login_link': self.generate_login_link(sub_user['code']),
                    'category': sub_user['category'],
                    'type': sub_user['type'],
                    'permissions': self.get_user_permissions(sub_user['code'])
                }
                created_users[base_type]['sub_users'].append(user_data)
        
        return created_users