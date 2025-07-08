from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User, UserCategory, NonIndividualType, ProfessionalType, UserRole, Company, UserCompanyAccess, UserRole
from utils.user_code_generator import UserCodeGenerator
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        if not username:
            flash('Please enter a username.', 'error')
            return render_template('login.html')
        
        # DUMMY LOGIN SYSTEM - Create/find user based on username
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Create hierarchical dummy user based on username
            try:
                username_lower = username.lower()
                
                # Determine user category and type based on username
                if any(word in username_lower for word in ['ca', 'cs', 'legal']):
                    category = UserCategory.PROFESSIONAL
                    if 'ca' in username_lower:
                        professional_type = ProfessionalType.CA
                        role = UserRole.CA
                    elif 'cs' in username_lower:
                        professional_type = ProfessionalType.CS
                        role = UserRole.AUDITOR  # Using existing role
                    elif 'legal' in username_lower:
                        professional_type = ProfessionalType.LEGAL
                        role = UserRole.LEGAL
                    else:
                        professional_type = ProfessionalType.CA
                        role = UserRole.CA
                    non_individual_type = None
                elif any(word in username_lower for word in ['company', 'corp', 'llp']):
                    category = UserCategory.NON_INDIVIDUAL
                    professional_type = None
                    if 'llp' in username_lower:
                        non_individual_type = NonIndividualType.LLP
                    else:
                        non_individual_type = NonIndividualType.COMPANY
                    role = UserRole.ADMIN if 'admin' in username_lower else UserRole.MANAGER
                else:
                    category = UserCategory.INDIVIDUAL
                    professional_type = None
                    non_individual_type = None
                    
                    # Determine role for individual users
                    if 'admin' in username_lower:
                        role = UserRole.ADMIN
                    elif 'account' in username_lower:
                        role = UserRole.ACCOUNTANT
                    elif 'audit' in username_lower:
                        role = UserRole.AUDITOR
                    elif 'manager' in username_lower:
                        role = UserRole.MANAGER
                    elif 'editor' in username_lower:
                        role = UserRole.EDITOR
                    else:
                        role = UserRole.VIEWER
                
                # Check if this is the first user (will be main admin)
                existing_users = User.query.count()
                is_admin = existing_users == 0 or 'admin' in username_lower
                
                user = User(
                    username=username,
                    email=f"{username}@accufin360.com",
                    password_hash=generate_password_hash("dummy123"),
                    first_name=username.split('_')[0].capitalize(),
                    last_name="User",
                    category=category,
                    non_individual_type=non_individual_type,
                    professional_type=professional_type,
                    role=role,
                    is_admin=is_admin,
                    is_verified=True
                )
                
                db.session.add(user)
                db.session.commit()
                
                # Create a default company for non-individual users
                if category == UserCategory.NON_INDIVIDUAL:
                    company_name = f"{user.first_name} {non_individual_type.value.upper()}"
                    company = Company(
                        name=company_name,
                        owner_user_id=user.id,
                        company_type=non_individual_type,
                        base_currency='USD',
                        financial_year_start='01-01'
                    )
                    
                    db.session.add(company)
                    db.session.commit()
                    
                    # Grant full access to the owner
                    access = UserCompanyAccess(
                        user_id=user.id,
                        company_id=company.id,
                        access_level='full',
                        can_view_reports=True,
                        can_edit_transactions=True,
                        can_manage_settings=True,
                        can_export_data=True,
                        granted_by=user.id
                    )
                    
                    db.session.add(access)
                    db.session.commit()
                
                flash(f'Welcome! Created {category.value} account for {username} with role: {role.value}', 'success')
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Dummy user creation error: {str(e)}")
                flash('Login failed. Please try again.', 'error')
                return render_template('login.html')
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact administrator.', 'error')
            return render_template('login.html')
        
        login_user(user, remember=remember)
        
        # Log successful login
        logging.info(f"User {username} logged in successfully with dummy login")
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        return redirect(url_for('main.dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role', 'viewer')
        
        # Validation
        if not all([username, email, password, confirm_password, first_name, last_name]):
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('register.html')
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                first_name=first_name,
                last_name=last_name,
                role=UserRole(role)
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    logging.info(f"User {username} logged out")
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    
    if not all([first_name, last_name, email]):
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('auth.profile'))
    
    # Check if email is already taken by another user
    existing_user = User.query.filter_by(email=email).first()
    if existing_user and existing_user.id != current_user.id:
        flash('Email already exists.', 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Profile update error: {str(e)}")
        flash('Profile update failed. Please try again.', 'error')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('auth.profile'))
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Password change error: {str(e)}")
        flash('Password change failed. Please try again.', 'error')
    
    return redirect(url_for('auth.profile'))
