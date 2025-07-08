"""
Admin Routes for User Management and Permissions
Comprehensive admin interface for the permissions matrix system
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import json
import logging
from datetime import datetime, timedelta
from app import db
from models import User, UserCategory, UserRole, NonIndividualType, ProfessionalType
from permissions_models import Permission, Module, UserPermission, UserProfile, UserInvitation, PermissionAuditLog
from services.permissions_manager import PermissionsManager

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
permissions_manager = PermissionsManager()

def admin_required(f):
    """Decorator to require admin access"""
    def admin_decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    admin_decorated_function.__name__ = f.__name__
    return admin_decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    """Main admin dashboard"""
    try:
        # Initialize permissions system if needed
        initialize_permissions_if_needed()
        # Get dashboard statistics
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'pending_kyc': 0,  # Simplified for now
            'total_permissions': 0,  # Simplified for now
            'recent_logins': User.query.filter(User.last_login.isnot(None)).order_by(User.last_login.desc()).limit(5).all(),
            'pending_invitations': 0  # Simplified for now
        }
        
        # Get recent audit activity - simplified for now
        recent_activity = []
        
        # Get users for simplified view
        users = User.query.filter(User.id != current_user.id).order_by(User.created_at.desc()).all()
        
        return render_template('admin/f_ai_admin_dashboard.html', stats=stats, users=users)
        
    except Exception as e:
        logging.error(f"Error loading admin dashboard: {str(e)}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('main.dashboard'))

@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """List all users with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        role = request.args.get('role', '')
        status = request.args.get('status', '')
        
        # Build query
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.email.contains(search),
                    User.first_name.contains(search),
                    User.last_name.contains(search)
                )
            )
        
        if category:
            query = query.filter(User.category == category)
        
        if role:
            query = query.filter(User.role == role)
        
        if status == 'active':
            query = query.filter(User.is_active == True)
        elif status == 'inactive':
            query = query.filter(User.is_active == False)
        
        # Paginate
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/users_list.html', 
                             users=users, 
                             search=search, 
                             category=category, 
                             role=role, 
                             status=status)
        
    except Exception as e:
        logging.error(f"Error loading users list: {str(e)}")
        flash('Error loading users', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """User detail and permissions management"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user permissions matrix
        permissions_matrix = permissions_manager.get_user_permissions_matrix(user_id)
        
        # Get all available modules and permissions
        modules = Module.query.filter_by(is_active=True).order_by(Module.name).all()
        permissions = Permission.query.filter_by(is_active=True).order_by(Permission.code).all()
        
        # Get user profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        # Get audit trail for this user
        audit_trail = permissions_manager.get_permissions_audit_trail(user_id=user_id, days=30)
        
        return render_template('admin/user_detail.html',
                             user=user,
                             profile=profile,
                             permissions_matrix=permissions_matrix,
                             modules=modules,
                             permissions=permissions,
                             audit_trail=audit_trail)
        
    except Exception as e:
        logging.error(f"Error loading user detail: {str(e)}")
        flash('Error loading user details', 'error')
        return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user with permissions"""
    if request.method == 'POST':
        try:
            user_data = {
                'username': request.form.get('username'),
                'email': request.form.get('email'),
                'password_hash': generate_password_hash(request.form.get('password', 'defaultpassword')),
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'category': UserCategory(request.form.get('category')),
                'role': UserRole(request.form.get('role')),
                'is_active': request.form.get('is_active') == 'on',
                'is_verified': request.form.get('is_verified') == 'on'
            }
            
            # Profile data
            profile_data = {
                'primary_email': request.form.get('primary_email') or user_data['email'],
                'primary_phone': request.form.get('primary_phone'),
                'secondary_email': request.form.get('secondary_email'),
                'secondary_phone': request.form.get('secondary_phone'),
                'kyc_status': request.form.get('kyc_status', 'pending')
            }
            
            user_data['profile'] = profile_data
            
            # Get permissions matrix from form
            permissions_matrix = {}
            for module_code in request.form.getlist('modules'):
                module_permissions = request.form.getlist(f'permissions_{module_code}')
                if module_permissions:
                    permissions_matrix[module_code] = module_permissions
            
            # Create user
            user = permissions_manager.create_user_with_permissions(user_data, permissions_matrix)
            
            if user:
                flash(f'User {user.email} created successfully', 'success')
                return redirect(url_for('admin.user_detail', user_id=user.id))
            else:
                flash('Failed to create user', 'error')
                
        except Exception as e:
            logging.error(f"Error creating user: {str(e)}")
            flash(f'Error creating user: {str(e)}', 'error')
    
    # GET request - show form
    modules = Module.query.filter_by(is_active=True).order_by(Module.name).all()
    permissions = Permission.query.filter_by(is_active=True).order_by(Permission.code).all()
    
    return render_template('admin/create_user.html', modules=modules, permissions=permissions)

@admin_bp.route('/users/<int:user_id>/permissions', methods=['POST'])
@login_required
@admin_required
def update_user_permissions(user_id):
    """Update user permissions via AJAX"""
    try:
        data = request.get_json()
        module_code = data.get('module')
        permission_code = data.get('permission')
        granted = data.get('granted', False)
        
        if granted:
            # Grant permission
            permissions_matrix = {module_code: [permission_code]}
            permissions_manager.assign_permissions_bulk(user_id, permissions_matrix, current_user.id)
            action = 'granted'
        else:
            # Revoke permission
            success = permissions_manager.revoke_permission(
                user_id, module_code, permission_code, current_user.id
            )
            if not success:
                return jsonify({'success': False, 'message': 'Failed to revoke permission'})
            action = 'revoked'
        
        return jsonify({
            'success': True,
            'message': f'Permission {permission_code} {action} for {module_code}'
        })
        
    except Exception as e:
        logging.error(f"Error updating permissions: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/invitations')
@login_required
@admin_required
def invitations_list():
    """List user invitations"""
    try:
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status', '')
        
        query = UserInvitation.query
        
        if status:
            query = query.filter(UserInvitation.status == status)
        
        invitations = query.order_by(UserInvitation.sent_at.desc()).paginate(
            page=page, per_page=25, error_out=False
        )
        
        return render_template('admin/invitations_list.html', invitations=invitations, status=status)
        
    except Exception as e:
        logging.error(f"Error loading invitations: {str(e)}")
        flash('Error loading invitations', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/invitations/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_invitation():
    """Create user invitation"""
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            phone = request.form.get('phone')
            intended_role = request.form.get('intended_role')
            message = request.form.get('message')
            expires_in_days = int(request.form.get('expires_in_days', 7))
            
            # Get permissions matrix
            permissions_matrix = {}
            for module_code in request.form.getlist('modules'):
                module_permissions = request.form.getlist(f'permissions_{module_code}')
                if module_permissions:
                    permissions_matrix[module_code] = module_permissions
            
            invitation = permissions_manager.create_user_invitation(
                invited_by=current_user.id,
                email=email,
                phone=phone,
                intended_role=intended_role,
                permissions_matrix=permissions_matrix,
                message=message,
                expires_in_days=expires_in_days
            )
            
            if invitation:
                flash(f'Invitation created: {invitation.invitation_code}', 'success')
                return redirect(url_for('admin.invitations_list'))
            else:
                flash('Failed to create invitation', 'error')
                
        except Exception as e:
            logging.error(f"Error creating invitation: {str(e)}")
            flash(f'Error creating invitation: {str(e)}', 'error')
    
    # GET request
    modules = Module.query.filter_by(is_active=True).order_by(Module.name).all()
    permissions = Permission.query.filter_by(is_active=True).order_by(Permission.code).all()
    
    return render_template('admin/create_invitation.html', modules=modules, permissions=permissions)

@admin_bp.route('/kyc')
@login_required
@admin_required
def kyc_management():
    """KYC verification management"""
    try:
        status_filter = request.args.get('status', 'pending')
        
        query = db.session.query(UserProfile, User).join(User, UserProfile.user_id == User.id)
        
        if status_filter:
            query = query.filter(UserProfile.kyc_status == status_filter)
        
        profiles = query.order_by(UserProfile.created_at.desc()).all()
        
        return render_template('admin/kyc_management.html', profiles=profiles, status_filter=status_filter)
        
    except Exception as e:
        logging.error(f"Error loading KYC management: {str(e)}")
        flash('Error loading KYC management', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/kyc/<int:user_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_kyc(user_id):
    """Verify user KYC"""
    try:
        document_type = request.form.get('document_type')
        document_number = request.form.get('document_number')
        document_path = request.form.get('document_path', '')
        notes = request.form.get('notes')
        
        success = permissions_manager.verify_kyc(
            user_id=user_id,
            document_type=document_type,
            document_number=document_number,
            document_path=document_path,
            verified_by=current_user.id,
            notes=notes
        )
        
        if success:
            flash('KYC verified successfully', 'success')
        else:
            flash('Failed to verify KYC', 'error')
            
        return redirect(url_for('admin.kyc_management'))
        
    except Exception as e:
        logging.error(f"Error verifying KYC: {str(e)}")
        flash(f'Error verifying KYC: {str(e)}', 'error')
        return redirect(url_for('admin.kyc_management'))

@admin_bp.route('/audit')
@login_required
@admin_required
def audit_trail():
    """View permissions audit trail"""
    try:
        days = request.args.get('days', 30, type=int)
        user_filter = request.args.get('user_id', type=int)
        action_filter = request.args.get('action', '')
        
        audit_logs = permissions_manager.get_permissions_audit_trail(user_id=user_filter, days=days)
        
        if action_filter:
            audit_logs = [log for log in audit_logs if log['action'] == action_filter]
        
        # Get users for filter dropdown
        users = User.query.filter_by(is_active=True).order_by(User.username).all()
        
        return render_template('admin/audit_trail.html', 
                             audit_logs=audit_logs, 
                             users=users,
                             days=days,
                             user_filter=user_filter,
                             action_filter=action_filter)
        
    except Exception as e:
        logging.error(f"Error loading audit trail: {str(e)}")
        flash('Error loading audit trail', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/permissions-matrix')
@login_required
@admin_required
def permissions_matrix():
    """View and manage permissions matrix"""
    try:
        # Get all modules and permissions
        modules = Module.query.filter_by(is_active=True).order_by(Module.name).all()
        permissions = Permission.query.filter_by(is_active=True).order_by(Permission.code).all()
        
        # Get permissions usage statistics
        stats = {}
        for module in modules:
            module_stats = {}
            for permission in permissions:
                count = UserPermission.query.filter_by(
                    module_id=module.id,
                    permission_id=permission.id,
                    is_granted=True
                ).count()
                module_stats[permission.code] = count
            stats[module.code] = module_stats
        
        return render_template('admin/permissions_matrix.html',
                             modules=modules,
                             permissions=permissions,
                             stats=stats)
        
    except Exception as e:
        logging.error(f"Error loading permissions matrix: {str(e)}")
        flash('Error loading permissions matrix', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active
        db.session.commit()
        
        status = "activated" if user.is_active else "deactivated"
        return jsonify({
            'success': True,
            'message': f'User {status} successfully',
            'is_active': user.is_active
        })
        
    except Exception as e:
        logging.error(f"Error toggling user status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_admin_stats():
    """API endpoint for admin dashboard stats"""
    try:
        stats = {
            'users': {
                'total': User.query.count(),
                'active': User.query.filter_by(is_active=True).count(),
                'new_this_week': User.query.filter(
                    User.created_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
            },
            'permissions': {
                'total_assignments': UserPermission.query.filter_by(is_granted=True).count(),
                'total_revocations': UserPermission.query.filter_by(is_granted=False).count()
            },
            'kyc': {
                'pending': UserProfile.query.filter_by(kyc_status='pending').count(),
                'verified': UserProfile.query.filter_by(kyc_status='verified').count(),
                'rejected': UserProfile.query.filter_by(kyc_status='rejected').count()
            },
            'invitations': {
                'sent': UserInvitation.query.filter_by(status='sent').count(),
                'accepted': UserInvitation.query.filter_by(status='accepted').count(),
                'expired': UserInvitation.query.filter_by(status='expired').count()
            }
        }
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        logging.error(f"Error getting admin stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/users')
@login_required
@admin_required
def api_users():
    """API endpoint for users list"""
    try:
        users = User.query.filter(User.id != current_user.id).order_by(User.created_at.desc()).all()
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'name': user.get_full_name(),
                'email': user.email,
                'role': user.role.name.replace('_', ' ').title() if user.role else 'Unknown',
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        return jsonify({'users': users_data})
    except Exception as e:
        return jsonify({'error': str(e)})

# Simplified User Management API Routes
@admin_bp.route('/create-user', methods=['POST'])
@login_required
@admin_required
def create_simple_user():
    """Create a simple sub-user with predefined permissions"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('role'):
            return jsonify({'success': False, 'message': 'Username and role are required'})
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        # Create user
        from werkzeug.security import generate_password_hash
        user = User(
            username=data['username'],
            email=data.get('email'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            password_hash=generate_password_hash('default123'),  # Default password
            role=UserRole(data['role']),
            parent_user_id=current_user.id,
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Apply permission preset
        preset = data.get('preset', 'view_only')
        apply_permission_preset(user.id, preset)
        
        return jsonify({'success': True, 'message': 'User created successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/user/<int:user_id>/permissions')
@login_required
@admin_required
def get_user_permissions_simple(user_id):
    """Get user permissions in simple format"""
    try:
        user = User.query.get_or_404(user_id)
        permissions = {}
        
        # Get user permissions by module
        user_perms = db.session.query(
            UserPermission, Module.name, Permission.name
        ).join(Module).join(Permission).filter(
            UserPermission.user_id == user_id,
            UserPermission.is_granted == True
        ).all()
        
        for perm, module_name, permission_name in user_perms:
            if module_name not in permissions:
                permissions[module_name] = []
            permissions[module_name].append(permission_name)
        
        return jsonify({'permissions': permissions})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@admin_bp.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status_simple(user_id):
    """Toggle user active status"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        user.is_active = data.get('active', not user.is_active)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User status updated'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

def apply_permission_preset(user_id, preset):
    """Apply predefined permission preset to user"""
    try:
        # Initialize permissions if needed
        permissions_manager.initialize_default_data()
        
        # Get all modules and permissions
        modules = Module.query.filter_by(is_active=True).all()
        
        # Define presets
        presets = {
            'full_access': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11'],
            'accounting_only': ['P1', 'P2', 'P4', 'P6', 'P7', 'P8'],  # Create, Edit, Update, View, Download, Upload
            'view_only': ['P6', 'P7'],  # View, Download
            'custom': []
        }
        
        preset_permissions = presets.get(preset, ['P6'])  # Default to view only
        
        # Apply permissions
        for module in modules:
            # Only apply to accounting-related modules for accounting_only preset
            if preset == 'accounting_only' and module.code not in ['ACC', 'INV', 'RPT']:
                continue
                
            for perm_code in preset_permissions:
                permission = Permission.query.filter_by(code=perm_code).first()
                if permission:
                    # Check if permission already exists
                    existing = UserPermission.query.filter_by(
                        user_id=user_id,
                        module_id=module.id,
                        permission_id=permission.id
                    ).first()
                    
                    if not existing:
                        user_perm = UserPermission(
                            user_id=user_id,
                            module_id=module.id,
                            permission_id=permission.id,
                            is_granted=True,
                            granted_by=current_user.id
                        )
                        db.session.add(user_perm)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error applying permission preset: {str(e)}")

# Initialize permissions system when needed
def initialize_permissions_if_needed():
    """Initialize permissions system if not already done"""
    try:
        # Simplified initialization - avoid potential table issues
        pass
    except Exception as e:
        logging.error(f"Error initializing permissions system: {str(e)}")