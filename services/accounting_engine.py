import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from app import db
from models import JournalEntry, ChartOfAccount, Company

class AccountingEngine:
    """Core accounting processing engine with double-entry bookkeeping"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.company_id = 1  # Default company ID
        self.default_accounts = self._get_default_accounts()
    
    def process_entries(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process accounting entries with double-entry validation"""
        try:
            entries = data['entries']
            processed_entries = []
            errors = []
            
            # Process each entry
            for entry in entries:
                try:
                    processed_entry = self._process_single_entry(entry)
                    if processed_entry:
                        processed_entries.append(processed_entry)
                except Exception as e:
                    error_msg = f"Error processing row {entry.get('row_number', 'unknown')}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            
            # Validate double-entry bookkeeping
            validation_result = self._validate_double_entry(processed_entries)
            
            # Save to database if validation passes
            if validation_result['is_valid']:
                saved_entries = self._save_journal_entries(processed_entries)
                
                result = {
                    'total_records': len(entries),
                    'processed_records': len(processed_entries),
                    'error_records': len(errors),
                    'saved_entries': len(saved_entries),
                    'validation_result': validation_result,
                    'errors': errors,
                    'log': f"Successfully processed {len(processed_entries)} entries"
                }
            else:
                result = {
                    'total_records': len(entries),
                    'processed_records': 0,
                    'error_records': len(entries),
                    'saved_entries': 0,
                    'validation_result': validation_result,
                    'errors': errors + validation_result['errors'],
                    'log': "Processing failed due to validation errors"
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in process_entries: {str(e)}")
            raise
    
    def _process_single_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single accounting entry"""
        try:
            # Extract and validate data
            entry_date = self._parse_date(entry.get('date'))
            description = entry.get('description', '').strip()
            account = self._resolve_account(entry.get('account', ''))
            debit_amount = self._parse_amount(entry.get('debit_amount', 0))
            credit_amount = self._parse_amount(entry.get('credit_amount', 0))
            amount = self._parse_amount(entry.get('amount', 0))
            reference = entry.get('reference', '').strip()
            
            # Validate required fields
            if not description:
                raise ValueError("Description is required")
            
            if not account:
                raise ValueError("Account is required")
            
            # Determine debit/credit amounts
            if debit_amount == 0 and credit_amount == 0 and amount != 0:
                # Auto-determine based on account type
                if self._is_debit_account(account):
                    debit_amount = amount
                else:
                    credit_amount = amount
            
            # Validate amounts
            if debit_amount == 0 and credit_amount == 0:
                raise ValueError("Either debit or credit amount must be specified")
            
            if debit_amount != 0 and credit_amount != 0:
                raise ValueError("Entry cannot have both debit and credit amounts")
            
            processed_entry = {
                'entry_date': entry_date,
                'description': description,
                'account': account,
                'debit_amount': debit_amount,
                'credit_amount': credit_amount,
                'reference_number': reference,
                'row_number': entry.get('row_number')
            }
            
            return processed_entry
            
        except Exception as e:
            self.logger.error(f"Error processing entry: {str(e)}")
            raise
    
    def _parse_date(self, date_value: Any) -> datetime:
        """Parse date from various formats"""
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            # Try common date formats
            formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
        
        # Default to today if parsing fails
        return datetime.now()
    
    def _parse_amount(self, amount_value: Any) -> Decimal:
        """Parse amount with proper decimal handling"""
        if amount_value is None:
            return Decimal('0.00')
        
        if isinstance(amount_value, (int, float)):
            return Decimal(str(amount_value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        if isinstance(amount_value, str):
            # Remove currency symbols and commas
            cleaned = amount_value.replace(',', '').replace('$', '').replace('₹', '').strip()
            try:
                return Decimal(cleaned).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except:
                return Decimal('0.00')
        
        return Decimal('0.00')
    
    def _resolve_account(self, account_name: str) -> Optional[str]:
        """Resolve account name to account code"""
        if not account_name:
            return None
        
        # First try exact match
        account = ChartOfAccount.query.filter_by(
            account_name=account_name.strip(),
            company_id=self.company_id
        ).first()
        
        if account:
            return account.account_code
        
        # Try partial match
        account = ChartOfAccount.query.filter(
            ChartOfAccount.account_name.ilike(f"%{account_name.strip()}%"),
            ChartOfAccount.company_id == self.company_id
        ).first()
        
        if account:
            return account.account_code
        
        # Use default account mapping
        return self.default_accounts.get(account_name.lower(), account_name)
    
    def _is_debit_account(self, account: str) -> bool:
        """Determine if account is typically a debit account"""
        debit_account_types = ['assets', 'expenses', 'dividends']
        
        # Check account type from chart of accounts
        account_obj = ChartOfAccount.query.filter_by(
            account_code=account,
            company_id=self.company_id
        ).first()
        
        if account_obj:
            return account_obj.account_type.lower() in debit_account_types
        
        # Default logic based on account name
        debit_indicators = ['cash', 'bank', 'asset', 'expense', 'cost', 'receivable']
        account_lower = account.lower()
        
        return any(indicator in account_lower for indicator in debit_indicators)
    
    def _validate_double_entry(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate double-entry bookkeeping rules"""
        try:
            total_debits = sum(entry['debit_amount'] for entry in entries)
            total_credits = sum(entry['credit_amount'] for entry in entries)
            
            balance_difference = abs(total_debits - total_credits)
            is_balanced = balance_difference < Decimal('0.01')
            
            errors = []
            if not is_balanced:
                errors.append(f"Total debits (${total_debits}) do not equal total credits (${total_credits})")
            
            # Check for empty entries
            empty_entries = [entry for entry in entries if not entry['description'] or not entry['account']]
            if empty_entries:
                errors.append(f"Found {len(empty_entries)} entries with missing description or account")
            
            # Check for zero amount entries
            zero_amount_entries = [entry for entry in entries if entry['debit_amount'] == 0 and entry['credit_amount'] == 0]
            if zero_amount_entries:
                errors.append(f"Found {len(zero_amount_entries)} entries with zero amounts")
            
            return {
                'is_valid': len(errors) == 0,
                'total_debits': float(total_debits),
                'total_credits': float(total_credits),
                'balance_difference': float(balance_difference),
                'errors': errors,
                'entry_count': len(entries)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating double-entry: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'entry_count': len(entries)
            }
    
    def _save_journal_entries(self, entries: List[Dict[str, Any]]) -> List[JournalEntry]:
        """Save journal entries to database"""
        try:
            saved_entries = []
            
            for entry in entries:
                # Get or create account
                account = self._get_or_create_account(entry['account'])
                
                journal_entry = JournalEntry(
                    company_id=self.company_id,
                    account_id=account.id,
                    created_by=1,  # TODO: Get from current user
                    entry_date=entry['entry_date'],
                    description=entry['description'],
                    reference_number=entry['reference_number'],
                    debit_amount=float(entry['debit_amount']),
                    credit_amount=float(entry['credit_amount']),
                    currency='USD',
                    is_posted=True
                )
                
                db.session.add(journal_entry)
                saved_entries.append(journal_entry)
            
            db.session.commit()
            
            self.logger.info(f"Successfully saved {len(saved_entries)} journal entries")
            return saved_entries
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error saving journal entries: {str(e)}")
            raise
    
    def _get_or_create_account(self, account_code: str) -> ChartOfAccount:
        """Get existing account or create new one"""
        account = ChartOfAccount.query.filter_by(
            account_code=account_code,
            company_id=self.company_id
        ).first()
        
        if not account:
            # Create new account
            account = ChartOfAccount(
                company_id=self.company_id,
                account_code=account_code,
                account_name=account_code,
                account_type='Assets',  # Default type
                is_active=True
            )
            db.session.add(account)
            db.session.flush()  # Get ID without committing
        
        return account
    
    def _get_default_accounts(self) -> Dict[str, str]:
        """Get default account mappings"""
        return {
            'cash': '1001',
            'bank': '1002',
            'accounts receivable': '1201',
            'inventory': '1301',
            'accounts payable': '2001',
            'sales': '4001',
            'cost of goods sold': '5001',
            'office expenses': '6001',
            'rent expense': '6002',
            'utilities expense': '6003',
            'depreciation expense': '6004'
        }
    
    def get_trial_balance(self, date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Generate trial balance"""
        try:
            # Default date range
            if not date_from:
                date_from = datetime(datetime.now().year, 1, 1)
            if not date_to:
                date_to = datetime.now()
            
            # Get all journal entries in date range
            entries = JournalEntry.query.filter(
                JournalEntry.entry_date >= date_from,
                JournalEntry.entry_date <= date_to,
                JournalEntry.is_posted == True
            ).all()
            
            # Calculate balances by account
            account_balances = {}
            for entry in entries:
                account_code = entry.account.account_code
                account_name = entry.account.account_name
                
                if account_code not in account_balances:
                    account_balances[account_code] = {
                        'account_code': account_code,
                        'account_name': account_name,
                        'debit_total': 0.0,
                        'credit_total': 0.0,
                        'balance': 0.0
                    }
                
                account_balances[account_code]['debit_total'] += entry.debit_amount
                account_balances[account_code]['credit_total'] += entry.credit_amount
            
            # Calculate net balances
            total_debits = 0.0
            total_credits = 0.0
            
            for account_code, balance in account_balances.items():
                net_balance = balance['debit_total'] - balance['credit_total']
                if net_balance > 0:
                    balance['balance'] = net_balance
                    total_debits += net_balance
                else:
                    balance['balance'] = abs(net_balance)
                    total_credits += abs(net_balance)
            
            return {
                'accounts': list(account_balances.values()),
                'total_debits': total_debits,
                'total_credits': total_credits,
                'is_balanced': abs(total_debits - total_credits) < 0.01,
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            self.logger.error(f"Error generating trial balance: {str(e)}")
            raise
