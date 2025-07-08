import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
import logging
from decimal import Decimal
import re

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency with proper symbol and formatting"""
    if currency == 'USD':
        return f"${amount:,.2f}"
    elif currency == 'EUR':
        return f"€{amount:,.2f}"
    elif currency == 'GBP':
        return f"£{amount:,.2f}"
    elif currency == 'INR':
        return f"₹{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_date(date_obj: datetime, format_str: str = '%Y-%m-%d') -> str:
    """Format date object to string"""
    if date_obj:
        return date_obj.strftime(format_str)
    return ''

def format_datetime(datetime_obj: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format datetime object to string"""
    if datetime_obj:
        return datetime_obj.strftime(format_str)
    return ''

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename with timestamp and UUID"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(original_filename)
    return f"{timestamp}_{unique_id}_{name}{ext}"

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing unsafe characters"""
    # Remove unsafe characters
    filename = re.sub(r'[^\w\s\-_\.]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    return filename

def parse_amount(amount_str: str) -> Decimal:
    """Parse amount string to Decimal"""
    if not amount_str:
        return Decimal('0.00')
    
    # Remove currency symbols and commas
    cleaned = str(amount_str).replace(',', '').replace('$', '').replace('₹', '').replace('€', '').replace('£', '').strip()
    
    try:
        return Decimal(cleaned).quantize(Decimal('0.01'))
    except:
        return Decimal('0.00')

def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage safely"""
    if total == 0:
        return 0.0
    return (part / total) * 100

def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    if os.path.exists(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)
    return 0.0

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_status_badge_class(status: str) -> str:
    """Get Bootstrap badge class for status"""
    status_classes = {
        'active': 'bg-success',
        'inactive': 'bg-secondary',
        'pending': 'bg-warning',
        'processing': 'bg-primary',
        'processed': 'bg-success',
        'error': 'bg-danger',
        'validation_error': 'bg-danger',
        'uploaded': 'bg-info',
        'validated': 'bg-success',
        'draft': 'bg-secondary',
        'sent': 'bg-primary',
        'paid': 'bg-success',
        'overdue': 'bg-danger',
        'cancelled': 'bg-dark'
    }
    return status_classes.get(status.lower(), 'bg-secondary')

def get_account_type_icon(account_type: str) -> str:
    """Get Font Awesome icon for account type"""
    type_icons = {
        'assets': 'fas fa-coins',
        'liabilities': 'fas fa-credit-card',
        'equity': 'fas fa-chart-pie',
        'revenue': 'fas fa-arrow-up',
        'expenses': 'fas fa-arrow-down',
        'income': 'fas fa-plus-circle',
        'cost': 'fas fa-minus-circle'
    }
    return type_icons.get(account_type.lower(), 'fas fa-file-invoice-dollar')

def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
    cleaned_phone = re.sub(r'[^\d\+]', '', phone)
    return bool(re.match(phone_pattern, cleaned_phone))

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def get_portal_permissions(user_role: str) -> List[str]:
    """Get list of portals user can access based on role"""
    portal_permissions = {
        'admin': ['admin', 'invoice', 'inventory', 'gst', 'audit', 'reports', 'ai_insights', 'legal'],
        'accountant': ['invoice', 'inventory', 'gst', 'reports', 'ai_insights'],
        'auditor': ['audit', 'reports'],
        'ca': ['invoice', 'gst', 'audit', 'reports'],
        'client_success': ['reports'],
        'legal': ['legal', 'reports'],
        'viewer': ['reports']
    }
    return portal_permissions.get(user_role.lower(), [])

def log_user_activity(user_id: int, action: str, details: str = '') -> None:
    """Log user activity for audit trail"""
    logger = logging.getLogger(__name__)
    logger.info(f"User {user_id} performed action: {action}. Details: {details}")

class ValidationError(Exception):
    """Custom validation error"""
    pass

class ProcessingError(Exception):
    """Custom processing error"""
    pass

def safe_division(numerator: float, denominator: float) -> float:
    """Perform safe division avoiding division by zero"""
    if denominator == 0:
        return 0.0
    return numerator / denominator

def round_currency(amount: float, currency: str = 'USD') -> float:
    """Round currency to appropriate decimal places"""
    if currency in ['JPY', 'KRW']:  # Currencies with no decimal places
        return round(amount)
    return round(amount, 2)

def get_financial_year(date: datetime) -> str:
    """Get financial year for a given date"""
    if date.month >= 4:  # April to March financial year
        return f"{date.year}-{date.year + 1}"
    else:
        return f"{date.year - 1}-{date.year}"

def format_number(number: float, decimal_places: int = 2) -> str:
    """Format number with thousand separators"""
    return f"{number:,.{decimal_places}f}"

def get_quarter(date: datetime) -> str:
    """Get quarter for a given date"""
    quarters = {
        1: 'Q1', 2: 'Q1', 3: 'Q1',
        4: 'Q2', 5: 'Q2', 6: 'Q2',
        7: 'Q3', 8: 'Q3', 9: 'Q3',
        10: 'Q4', 11: 'Q4', 12: 'Q4'
    }
    return quarters.get(date.month, 'Q1')

def create_audit_entry(user_id: int, action: str, table_name: str = None, 
                      record_id: int = None, old_values: Dict = None, 
                      new_values: Dict = None) -> Dict[str, Any]:
    """Create audit entry dictionary"""
    return {
        'user_id': user_id,
        'action': action,
        'table_name': table_name,
        'record_id': record_id,
        'old_values': str(old_values) if old_values else None,
        'new_values': str(new_values) if new_values else None,
        'timestamp': datetime.utcnow(),
        'ip_address': None,  # To be filled from request
        'user_agent': None   # To be filled from request
    }
