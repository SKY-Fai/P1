import pandas as pd
import openpyxl
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

class FileProcessor:
    """Handles file processing and data extraction for AccuFin360"""
    
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileProcessor.ALLOWED_EXTENSIONS
    
    def extract_data(self, file_path: str) -> Dict[str, Any]:
        """Extract data from uploaded file"""
        try:
            file_extension = file_path.rsplit('.', 1)[1].lower()
            
            if file_extension == 'csv':
                return self._process_csv(file_path)
            elif file_extension in ['xlsx', 'xls']:
                return self._process_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            self.logger.error(f"Error extracting data from {file_path}: {str(e)}")
            raise
    
    def _process_csv(self, file_path: str) -> Dict[str, Any]:
        """Process CSV file and extract accounting data"""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Clean and normalize data
            df = self._clean_dataframe(df)
            
            # Extract accounting entries
            entries = self._extract_accounting_entries(df)
            
            return {
                'file_type': 'csv',
                'total_rows': len(df),
                'entries': entries,
                'columns': df.columns.tolist(),
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing CSV file {file_path}: {str(e)}")
            raise
    
    def _process_excel(self, file_path: str) -> Dict[str, Any]:
        """Process Excel file and extract accounting data"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Clean and normalize data
            df = self._clean_dataframe(df)
            
            # Extract accounting entries
            entries = self._extract_accounting_entries(df)
            
            return {
                'file_type': 'excel',
                'total_rows': len(df),
                'entries': entries,
                'columns': df.columns.tolist(),
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing Excel file {file_path}: {str(e)}")
            raise
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize DataFrame"""
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Remove empty columns
        df = df.dropna(axis=1, how='all')
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
        
        # Convert date columns
        date_columns = ['date', 'transaction_date', 'entry_date', 'invoice_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert numeric columns
        numeric_columns = ['amount', 'debit', 'credit', 'debit_amount', 'credit_amount', 'total']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _extract_accounting_entries(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract accounting entries from DataFrame"""
        entries = []
        
        try:
            # Standard column mappings
            column_mapping = {
                'date': ['date', 'transaction_date', 'entry_date'],
                'description': ['description', 'narration', 'particulars'],
                'account': ['account', 'account_name', 'account_code'],
                'debit': ['debit', 'debit_amount', 'dr'],
                'credit': ['credit', 'credit_amount', 'cr'],
                'amount': ['amount', 'total', 'value'],
                'reference': ['reference', 'ref_no', 'voucher_no']
            }
            
            # Find actual column names
            actual_columns = {}
            for standard_col, possible_names in column_mapping.items():
                for possible_name in possible_names:
                    if possible_name.lower() in [col.lower() for col in df.columns]:
                        actual_columns[standard_col] = possible_name
                        break
            
            # Extract entries
            for index, row in df.iterrows():
                entry = {
                    'row_number': index + 1,
                    'date': self._get_value(row, actual_columns.get('date')),
                    'description': self._get_value(row, actual_columns.get('description')),
                    'account': self._get_value(row, actual_columns.get('account')),
                    'debit_amount': self._get_numeric_value(row, actual_columns.get('debit')),
                    'credit_amount': self._get_numeric_value(row, actual_columns.get('credit')),
                    'amount': self._get_numeric_value(row, actual_columns.get('amount')),
                    'reference': self._get_value(row, actual_columns.get('reference')),
                    'raw_data': row.to_dict()
                }
                
                # Skip empty entries
                if not any([entry['description'], entry['account'], entry['debit_amount'], 
                           entry['credit_amount'], entry['amount']]):
                    continue
                
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Error extracting accounting entries: {str(e)}")
            raise
    
    def _get_value(self, row: pd.Series, column: Optional[str]) -> Optional[str]:
        """Get string value from row"""
        if column and column in row.index:
            value = row[column]
            if pd.isna(value):
                return None
            return str(value).strip()
        return None
    
    def _get_numeric_value(self, row: pd.Series, column: Optional[str]) -> float:
        """Get numeric value from row"""
        if column and column in row.index:
            value = row[column]
            if pd.isna(value):
                return 0.0
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    
    def validate_template(self, file_path: str, template_type: str = 'general') -> Dict[str, Any]:
        """Validate file against template requirements"""
        try:
            data = self.extract_data(file_path)
            
            # Define required columns for different templates
            required_columns = {
                'general': ['date', 'description', 'account'],
                'invoice': ['invoice_date', 'customer_name', 'amount'],
                'inventory': ['item_code', 'item_name', 'quantity'],
                'gst': ['gstin', 'invoice_number', 'taxable_amount']
            }
            
            template_columns = required_columns.get(template_type, required_columns['general'])
            
            # Check for required columns
            missing_columns = []
            for req_col in template_columns:
                if not any(req_col.lower() in col.lower() for col in data['columns']):
                    missing_columns.append(req_col)
            
            validation_result = {
                'is_valid': len(missing_columns) == 0,
                'missing_columns': missing_columns,
                'total_rows': data['total_rows'],
                'columns_found': data['columns'],
                'template_type': template_type
            }
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating template: {str(e)}")
            return {
                'is_valid': False,
                'error': str(e),
                'template_type': template_type
            }
    
    def get_processing_summary(self, file_path: str) -> Dict[str, Any]:
        """Get summary of file processing"""
        try:
            data = self.extract_data(file_path)
            
            # Calculate summary statistics
            entries = data['entries']
            total_debits = sum(entry['debit_amount'] for entry in entries)
            total_credits = sum(entry['credit_amount'] for entry in entries)
            
            summary = {
                'total_entries': len(entries),
                'total_debits': total_debits,
                'total_credits': total_credits,
                'balance_difference': abs(total_debits - total_credits),
                'is_balanced': abs(total_debits - total_credits) < 0.01,
                'unique_accounts': len(set(entry['account'] for entry in entries if entry['account'])),
                'date_range': self._get_date_range(entries),
                'file_type': data['file_type']
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting processing summary: {str(e)}")
            raise
    
    def _get_date_range(self, entries: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get date range from entries"""
        dates = [entry['date'] for entry in entries if entry['date']]
        
        if not dates:
            return {'start': None, 'end': None}
        
        valid_dates = [date for date in dates if pd.notna(date)]
        
        if not valid_dates:
            return {'start': None, 'end': None}
        
        return {
            'start': min(valid_dates).strftime('%Y-%m-%d'),
            'end': max(valid_dates).strftime('%Y-%m-%d')
        }
