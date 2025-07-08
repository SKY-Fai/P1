import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import re

class ValidationEngine:
    """Data validation engine for financial data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_rules = self._load_validation_rules()
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Main validation function for uploaded files"""
        try:
            # Extract file extension
            file_extension = file_path.rsplit('.', 1)[1].lower()
            
            # Load data based on file type
            if file_extension == 'csv':
                df = pd.read_csv(file_path)
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                return {
                    'is_valid': False,
                    'errors': [f'Unsupported file format: {file_extension}']
                }
            
            # Run validation checks
            validation_results = self._run_validation_checks(df)
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating file {file_path}: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f'File validation error: {str(e)}']
            }
    
    def _run_validation_checks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run comprehensive validation checks"""
        errors = []
        warnings = []
        
        # Structure validation
        structure_errors = self._validate_structure(df)
        errors.extend(structure_errors)
        
        # Data type validation
        data_type_errors = self._validate_data_types(df)
        errors.extend(data_type_errors)
        
        # Business logic validation
        business_errors = self._validate_business_logic(df)
        errors.extend(business_errors)
        
        # Completeness validation
        completeness_errors = self._validate_completeness(df)
        errors.extend(completeness_errors)
        
        # Consistency validation
        consistency_errors = self._validate_consistency(df)
        errors.extend(consistency_errors)
        
        # Range validation
        range_errors = self._validate_ranges(df)
        errors.extend(range_errors)
        
        # Format validation
        format_errors = self._validate_formats(df)
        errors.extend(format_errors)
        
        # Duplicate validation
        duplicate_errors = self._validate_duplicates(df)
        warnings.extend(duplicate_errors)
        
        # Calculate validation score
        total_checks = len(df) * 10  # Approximate number of checks
        error_count = len(errors)
        validation_score = max(0, (total_checks - error_count) / total_checks * 100)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validation_score': validation_score,
            'total_rows': len(df),
            'columns': list(df.columns),
            'validation_summary': self._generate_validation_summary(df, errors, warnings)
        }
    
    def _validate_structure(self, df: pd.DataFrame) -> List[str]:
        """Validate file structure"""
        errors = []
        
        # Check if file is empty
        if df.empty:
            errors.append("File is empty")
            return errors
        
        # Check minimum required columns
        required_columns = ['date', 'description', 'amount']
        missing_columns = []
        
        for req_col in required_columns:
            if not any(req_col.lower() in col.lower() for col in df.columns):
                missing_columns.append(req_col)
        
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Check for completely empty columns
        empty_columns = [col for col in df.columns if df[col].isna().all()]
        if empty_columns:
            errors.append(f"Found empty columns: {', '.join(empty_columns)}")
        
        # Check for duplicate column names
        if len(df.columns) != len(set(df.columns)):
            errors.append("Duplicate column names found")
        
        return errors
    
    def _validate_data_types(self, df: pd.DataFrame) -> List[str]:
        """Validate data types"""
        errors = []
        
        # Find potential numeric columns
        numeric_columns = ['amount', 'debit', 'credit', 'balance', 'quantity', 'price', 'total']
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Check numeric columns
            if any(num_col in col_lower for num_col in numeric_columns):
                non_numeric_count = 0
                for idx, value in df[col].items():
                    if pd.notna(value) and not self._is_numeric(value):
                        non_numeric_count += 1
                
                if non_numeric_count > 0:
                    errors.append(f"Column '{col}' contains {non_numeric_count} non-numeric values")
            
            # Check date columns
            if any(date_col in col_lower for date_col in ['date', 'time']):
                invalid_dates = 0
                for idx, value in df[col].items():
                    if pd.notna(value) and not self._is_valid_date(value):
                        invalid_dates += 1
                
                if invalid_dates > 0:
                    errors.append(f"Column '{col}' contains {invalid_dates} invalid date values")
        
        return errors
    
    def _validate_business_logic(self, df: pd.DataFrame) -> List[str]:
        """Validate business logic rules"""
        errors = []
        
        # Find debit and credit columns
        debit_col = self._find_column(df, ['debit', 'dr', 'debit_amount'])
        credit_col = self._find_column(df, ['credit', 'cr', 'credit_amount'])
        
        if debit_col and credit_col:
            # Check double-entry bookkeeping
            total_debits = pd.to_numeric(df[debit_col], errors='coerce').sum()
            total_credits = pd.to_numeric(df[credit_col], errors='coerce').sum()
            
            if abs(total_debits - total_credits) > 0.01:
                errors.append(f"Double-entry bookkeeping violation: Total debits (${total_debits:.2f}) != Total credits (${total_credits:.2f})")
            
            # Check for entries with both debit and credit
            both_present = 0
            for idx, row in df.iterrows():
                debit_val = pd.to_numeric(row[debit_col], errors='coerce')
                credit_val = pd.to_numeric(row[credit_col], errors='coerce')
                
                if pd.notna(debit_val) and pd.notna(credit_val) and debit_val > 0 and credit_val > 0:
                    both_present += 1
            
            if both_present > 0:
                errors.append(f"Found {both_present} entries with both debit and credit amounts")
        
        # Check for negative amounts where they shouldn't be
        amount_col = self._find_column(df, ['amount', 'total', 'value'])
        if amount_col:
            negative_amounts = (pd.to_numeric(df[amount_col], errors='coerce') < 0).sum()
            if negative_amounts > 0:
                errors.append(f"Found {negative_amounts} negative amounts")
        
        return errors
    
    def _validate_completeness(self, df: pd.DataFrame) -> List[str]:
        """Validate data completeness"""
        errors = []
        
        # Check for required fields
        required_fields = {
            'description': ['description', 'narration', 'particulars'],
            'amount': ['amount', 'debit', 'credit', 'total'],
            'date': ['date', 'transaction_date', 'entry_date']
        }
        
        for field_name, possible_columns in required_fields.items():
            found_col = self._find_column(df, possible_columns)
            if found_col:
                null_count = df[found_col].isna().sum()
                if null_count > 0:
                    errors.append(f"Field '{found_col}' has {null_count} missing values")
        
        # Check for completely empty rows
        empty_rows = df.isna().all(axis=1).sum()
        if empty_rows > 0:
            errors.append(f"Found {empty_rows} completely empty rows")
        
        return errors
    
    def _validate_consistency(self, df: pd.DataFrame) -> List[str]:
        """Validate data consistency"""
        errors = []
        
        # Check date consistency
        date_col = self._find_column(df, ['date', 'transaction_date', 'entry_date'])
        if date_col:
            dates = pd.to_datetime(df[date_col], errors='coerce')
            valid_dates = dates.dropna()
            
            if len(valid_dates) > 1:
                date_range = valid_dates.max() - valid_dates.min()
                if date_range.days > 365:
                    errors.append(f"Date range spans {date_range.days} days - may indicate data inconsistency")
                
                # Check for future dates
                future_dates = (valid_dates > datetime.now()).sum()
                if future_dates > 0:
                    errors.append(f"Found {future_dates} future dates")
        
        # Check account code consistency
        account_col = self._find_column(df, ['account', 'account_code', 'account_name'])
        if account_col:
            # Check for inconsistent account code formats
            account_codes = df[account_col].dropna().astype(str)
            if len(account_codes) > 0:
                # Check if all codes follow similar format
                formats = set()
                for code in account_codes:
                    if re.match(r'^\d+$', code):
                        formats.add('numeric')
                    elif re.match(r'^[A-Z]+\d+$', code):
                        formats.add('alpha_numeric')
                    else:
                        formats.add('other')
                
                if len(formats) > 1:
                    errors.append(f"Inconsistent account code formats found: {', '.join(formats)}")
        
        return errors
    
    def _validate_ranges(self, df: pd.DataFrame) -> List[str]:
        """Validate value ranges"""
        errors = []
        
        # Check for unreasonable amounts
        amount_cols = ['amount', 'debit', 'credit', 'total', 'balance']
        
        for col in df.columns:
            if any(amount_col in col.lower() for amount_col in amount_cols):
                numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()
                
                if len(numeric_values) > 0:
                    # Check for extremely large amounts
                    max_val = numeric_values.max()
                    if max_val > 1000000000:  # 1 billion
                        errors.append(f"Column '{col}' contains extremely large values (max: ${max_val:,.2f})")
                    
                    # Check for extremely small amounts
                    min_positive = numeric_values[numeric_values > 0].min() if (numeric_values > 0).any() else 0
                    if min_positive > 0 and min_positive < 0.01:
                        errors.append(f"Column '{col}' contains very small values (min: ${min_positive:.4f})")
        
        return errors
    
    def _validate_formats(self, df: pd.DataFrame) -> List[str]:
        """Validate data formats"""
        errors = []
        
        # Check phone number format
        phone_col = self._find_column(df, ['phone', 'telephone', 'mobile'])
        if phone_col:
            invalid_phones = 0
            for value in df[phone_col].dropna():
                if not self._is_valid_phone(str(value)):
                    invalid_phones += 1
            
            if invalid_phones > 0:
                errors.append(f"Column '{phone_col}' contains {invalid_phones} invalid phone numbers")
        
        # Check email format
        email_col = self._find_column(df, ['email', 'email_address'])
        if email_col:
            invalid_emails = 0
            for value in df[email_col].dropna():
                if not self._is_valid_email(str(value)):
                    invalid_emails += 1
            
            if invalid_emails > 0:
                errors.append(f"Column '{email_col}' contains {invalid_emails} invalid email addresses")
        
        return errors
    
    def _validate_duplicates(self, df: pd.DataFrame) -> List[str]:
        """Validate for duplicate records"""
        warnings = []
        
        # Check for duplicate rows
        duplicate_rows = df.duplicated().sum()
        if duplicate_rows > 0:
            warnings.append(f"Found {duplicate_rows} duplicate rows")
        
        # Check for duplicate reference numbers
        ref_col = self._find_column(df, ['reference', 'ref_no', 'voucher_no', 'transaction_id'])
        if ref_col:
            duplicate_refs = df[ref_col].duplicated().sum()
            if duplicate_refs > 0:
                warnings.append(f"Found {duplicate_refs} duplicate reference numbers")
        
        return warnings
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column by possible names"""
        for col in df.columns:
            if any(name.lower() in col.lower() for name in possible_names):
                return col
        return None
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric"""
        try:
            float(str(value).replace(',', '').replace('$', '').replace('₹', ''))
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_valid_date(self, value: Any) -> bool:
        """Check if value is a valid date"""
        if pd.isna(value):
            return False
        
        if isinstance(value, datetime):
            return True
        
        try:
            pd.to_datetime(value)
            return True
        except:
            return False
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Check if phone number is valid"""
        # Simple phone validation
        phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
        cleaned_phone = re.sub(r'[^\d\+]', '', phone)
        return bool(re.match(phone_pattern, cleaned_phone))
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if email is valid"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    def _generate_validation_summary(self, df: pd.DataFrame, errors: List[str], warnings: List[str]) -> Dict[str, Any]:
        """Generate validation summary"""
        return {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'error_count': len(errors),
            'warning_count': len(warnings),
            'data_quality_score': max(0, 100 - len(errors) * 5 - len(warnings) * 2),
            'completeness_score': self._calculate_completeness_score(df),
            'consistency_score': self._calculate_consistency_score(df)
        }
    
    def _calculate_completeness_score(self, df: pd.DataFrame) -> float:
        """Calculate data completeness score"""
        total_cells = df.size
        missing_cells = df.isna().sum().sum()
        return ((total_cells - missing_cells) / total_cells) * 100 if total_cells > 0 else 0
    
    def _calculate_consistency_score(self, df: pd.DataFrame) -> float:
        """Calculate data consistency score"""
        # Simple consistency score based on data types
        score = 100
        
        for col in df.columns:
            unique_types = set()
            for value in df[col].dropna():
                unique_types.add(type(value).__name__)
            
            if len(unique_types) > 1:
                score -= 10
        
        return max(0, score)
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules configuration"""
        return {
            'required_columns': ['date', 'description', 'amount'],
            'numeric_columns': ['amount', 'debit', 'credit', 'balance', 'quantity', 'price'],
            'date_columns': ['date', 'transaction_date', 'entry_date'],
            'max_amount': 1000000000,  # 1 billion
            'min_amount': 0.01,
            'max_date_range_days': 365,
            'phone_pattern': r'^[\+]?[1-9][\d]{0,15}$',
            'email_pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        }
