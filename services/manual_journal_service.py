"""
Manual Journal Entry Service - F-AI Accountant
Enhanced manual journal entry system with ledger mapping, creation, and approval workflow
"""

import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import uuid

from app import db
from models import *
from services.automated_accounting_engine import AutomatedAccountingEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JournalEntryStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"

class LedgerAccountType(Enum):
    ASSETS = "assets"
    LIABILITIES = "liabilities"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSES = "expenses"

@dataclass
class ManualJournalEntry:
    """Represents a manual journal entry with approval workflow"""
    entry_id: str
    entry_date: datetime
    reference_number: str
    description: str
    debit_entries: List[Dict[str, Any]]
    credit_entries: List[Dict[str, Any]]
    total_debit: Decimal
    total_credit: Decimal
    status: JournalEntryStatus
    created_by: int
    created_at: datetime
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    posted_by: Optional[int] = None
    posted_at: Optional[datetime] = None
    notes: str = ""
    attachments: List[str] = None

@dataclass
class LedgerAccount:
    """Represents a ledger account"""
    account_code: str
    account_name: str
    account_type: LedgerAccountType
    parent_account: Optional[str]
    description: str
    is_active: bool
    created_by: int
    created_at: datetime
    opening_balance: Decimal = Decimal('0.00')
    current_balance: Decimal = Decimal('0.00')

class AccountingRules:
    """
    Comprehensive accounting rules validation system
    """
    
    @staticmethod
    def get_account_normal_balance(account_type: str) -> str:
        """Get the normal balance for an account type"""
        normal_balances = {
            'assets': 'debit',
            'expenses': 'debit',
            'liabilities': 'credit',
            'equity': 'credit',
            'revenue': 'credit'
        }
        return normal_balances.get(account_type.lower(), 'debit')
    
    @staticmethod
    def get_debit_credit_effect(account_type: str, transaction_type: str) -> Dict[str, str]:
        """Get the effect of debit/credit on account balance"""
        effects = {
            'assets': {
                'debit': 'increase',
                'credit': 'decrease'
            },
            'expenses': {
                'debit': 'increase', 
                'credit': 'decrease'
            },
            'liabilities': {
                'debit': 'decrease',
                'credit': 'increase'
            },
            'equity': {
                'debit': 'decrease',
                'credit': 'increase'
            },
            'revenue': {
                'debit': 'decrease',
                'credit': 'increase'
            }
        }
        return effects.get(account_type.lower(), {'debit': 'increase', 'credit': 'decrease'})
    
    @staticmethod
    def validate_double_entry(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate double-entry principle"""
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')
        
        for entry in entries:
            debit_amount = Decimal(str(entry.get('debit_amount', 0)))
            credit_amount = Decimal(str(entry.get('credit_amount', 0)))
            
            total_debits += debit_amount
            total_credits += credit_amount
        
        difference = total_debits - total_credits
        
        return {
            'is_balanced': abs(difference) < Decimal('0.01'),
            'total_debits': float(total_debits),
            'total_credits': float(total_credits),
            'difference': float(difference),
            'error_message': f"Debits ({total_debits}) must equal Credits ({total_credits})" if abs(difference) >= Decimal('0.01') else None
        }
    
    @staticmethod
    def detect_transaction_pattern(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect common transaction patterns"""
        if len(entries) < 2:
            return {'pattern': 'insufficient_entries', 'description': 'Need at least 2 entries'}
        
        account_types = []
        for entry in entries:
            account_type = entry.get('account_type', '').lower()
            debit_amount = Decimal(str(entry.get('debit_amount', 0)))
            credit_amount = Decimal(str(entry.get('credit_amount', 0)))
            
            if debit_amount > 0:
                account_types.append(f"{account_type}_debit")
            if credit_amount > 0:
                account_types.append(f"{account_type}_credit")
        
        # Common patterns
        patterns = {
            ('assets_debit', 'revenue_credit'): {
                'pattern': 'cash_sale',
                'description': 'Cash Sale - Asset increases, Revenue increases'
            },
            ('expenses_debit', 'assets_credit'): {
                'pattern': 'expense_payment',
                'description': 'Expense Payment - Expense increases, Asset decreases'
            },
            ('assets_debit', 'liabilities_credit'): {
                'pattern': 'asset_on_credit',
                'description': 'Asset Purchase on Credit - Asset increases, Liability increases'
            },
            ('liabilities_debit', 'assets_credit'): {
                'pattern': 'liability_payment',
                'description': 'Liability Payment - Liability decreases, Asset decreases'
            },
            ('expenses_debit', 'liabilities_credit'): {
                'pattern': 'expense_on_credit',
                'description': 'Expense on Credit - Expense increases, Liability increases'
            }
        }
        
        account_types_tuple = tuple(sorted(account_types))
        pattern_info = patterns.get(account_types_tuple, {
            'pattern': 'custom_transaction',
            'description': 'Custom Transaction Pattern'
        })
        
        return pattern_info

class ManualJournalService:
    """
    Enhanced manual journal entry service with comprehensive accounting rules validation and review workflow
    """
    
    def __init__(self, company_id: int, user_id: int):
        self.company_id = company_id
        self.user_id = user_id
        self.accounting_engine = AutomatedAccountingEngine(company_id, user_id)
        self.accounting_rules = AccountingRules()
    
    def validate_journal_entry_comprehensive(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of journal entry with accounting rules
        """
        try:
            entries = entry_data.get('entries', [])
            
            # 1. Basic validation
            if len(entries) < 2:
                return {
                    'is_valid': False,
                    'errors': ['Journal entry must have at least 2 entries'],
                    'warnings': [],
                    'validation_details': {}
                }
            
            # 2. Validate double-entry principle
            double_entry_validation = self.accounting_rules.validate_double_entry(entries)
            
            # 3. Get chart of accounts for validation
            chart_of_accounts = self.get_standard_chart_of_accounts()
            account_lookup = {acc['account_code']: acc for acc in chart_of_accounts}
            
            # 4. Validate each entry
            entry_validations = []
            warnings = []
            errors = []
            
            for i, entry in enumerate(entries):
                entry_validation = self._validate_single_entry(entry, account_lookup, i + 1)
                entry_validations.append(entry_validation)
                
                if entry_validation.get('errors'):
                    errors.extend(entry_validation['errors'])
                if entry_validation.get('warnings'):
                    warnings.extend(entry_validation['warnings'])
            
            # 5. Detect transaction pattern
            pattern_info = self.accounting_rules.detect_transaction_pattern(entries)
            
            # 6. Additional business logic validation
            business_validation = self._validate_business_logic(entry_data, entries)
            
            # 7. Check for unusual amounts or account combinations
            anomaly_check = self._check_for_anomalies(entries, account_lookup)
            
            validation_result = {
                'is_valid': len(errors) == 0 and double_entry_validation['is_balanced'],
                'errors': errors,
                'warnings': warnings,
                'validation_details': {
                    'double_entry': double_entry_validation,
                    'transaction_pattern': pattern_info,
                    'entry_validations': entry_validations,
                    'business_validation': business_validation,
                    'anomaly_check': anomaly_check,
                    'accounting_compliance': self._check_accounting_compliance(entries, account_lookup)
                }
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in journal entry validation: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f'Validation error: {str(e)}'],
                'warnings': [],
                'validation_details': {}
            }
    
    def _validate_single_entry(self, entry: Dict[str, Any], account_lookup: Dict[str, Any], entry_number: int) -> Dict[str, Any]:
        """Validate a single journal entry line"""
        errors = []
        warnings = []
        
        account_code = entry.get('account_code', '').strip()
        debit_amount = entry.get('debit_amount', 0)
        credit_amount = entry.get('credit_amount', 0)
        description = entry.get('description', '').strip()
        
        # Validate account code
        if not account_code:
            errors.append(f"Entry {entry_number}: Account code is required")
        elif account_code not in account_lookup:
            errors.append(f"Entry {entry_number}: Invalid account code '{account_code}'")
        
        # Validate amounts
        if not debit_amount and not credit_amount:
            errors.append(f"Entry {entry_number}: Either debit or credit amount is required")
        elif debit_amount and credit_amount:
            errors.append(f"Entry {entry_number}: Cannot have both debit and credit amounts")
        elif debit_amount < 0 or credit_amount < 0:
            errors.append(f"Entry {entry_number}: Amounts cannot be negative")
        
        # Validate description
        if not description:
            warnings.append(f"Entry {entry_number}: Description is recommended for clarity")
        elif len(description) < 5:
            warnings.append(f"Entry {entry_number}: Description should be more descriptive")
        
        # Account-specific validations
        if account_code in account_lookup:
            account_info = account_lookup[account_code]
            account_type = account_info.get('account_type', '').lower()
            
            # Check for unusual debit/credit patterns
            normal_balance = self.accounting_rules.get_account_normal_balance(account_type)
            
            if debit_amount > 0 and normal_balance == 'credit':
                warnings.append(f"Entry {entry_number}: Unusual debit to {account_type} account (normal balance is credit)")
            elif credit_amount > 0 and normal_balance == 'debit':
                warnings.append(f"Entry {entry_number}: Unusual credit to {account_type} account (normal balance is debit)")
        
        return {
            'entry_number': entry_number,
            'errors': errors,
            'warnings': warnings,
            'account_code': account_code,
            'amount': debit_amount or credit_amount,
            'type': 'debit' if debit_amount > 0 else 'credit'
        }
    
    def _validate_business_logic(self, entry_data: Dict[str, Any], entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate business logic rules"""
        warnings = []
        errors = []
        
        # Check entry date
        entry_date = entry_data.get('date')
        if entry_date:
            try:
                parsed_date = datetime.strptime(entry_date, '%Y-%m-%d')
                
                # Future date warning
                if parsed_date > datetime.now():
                    warnings.append("Entry date is in the future")
                
                # Very old date warning
                if parsed_date < datetime.now() - timedelta(days=365):
                    warnings.append("Entry date is more than 1 year old")
                    
            except ValueError:
                errors.append("Invalid date format")
        
        # Check reference number uniqueness
        reference = entry_data.get('reference')
        if reference:
            # In a real system, check database for duplicate reference numbers
            pass
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def _check_for_anomalies(self, entries: List[Dict[str, Any]], account_lookup: Dict[str, Any]) -> Dict[str, Any]:
        """Check for unusual patterns or amounts"""
        warnings = []
        info = []
        
        # Check for large amounts
        total_amount = sum(
            float(entry.get('debit_amount', 0)) + float(entry.get('credit_amount', 0))
            for entry in entries
        )
        
        if total_amount > 100000:  # Large transaction threshold
            warnings.append(f"Large transaction amount: ₹{total_amount:,.2f}")
        
        # Check for round numbers (might indicate estimates)
        for entry in entries:
            amount = float(entry.get('debit_amount', 0)) or float(entry.get('credit_amount', 0))
            if amount > 0 and amount % 1000 == 0:
                info.append(f"Round number detected: ₹{amount:,.2f} (verify if estimate)")
        
        # Check account type diversity
        account_types = set()
        for entry in entries:
            account_code = entry.get('account_code', '')
            if account_code in account_lookup:
                account_types.add(account_lookup[account_code].get('account_type', ''))
        
        if len(account_types) < 2:
            info.append("Transaction involves similar account types - verify transaction logic")
        
        return {
            'warnings': warnings,
            'info': info,
            'total_transaction_amount': total_amount,
            'account_types_involved': list(account_types)
        }
    
    def _check_accounting_compliance(self, entries: List[Dict[str, Any]], account_lookup: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with accounting standards"""
        compliance_issues = []
        compliance_score = 100
        
        # Check for proper account usage
        cash_accounts = ['1000', '1020']  # Cash and bank accounts
        has_cash_flow = any(entry.get('account_code') in cash_accounts for entry in entries)
        
        revenue_accounts = ['4000', '4010', '4100']  # Revenue accounts
        has_revenue = any(entry.get('account_code') in revenue_accounts for entry in entries)
        
        # Revenue recognition principle
        if has_revenue:
            # Check if there's a corresponding asset or cash entry
            if not has_cash_flow:
                asset_accounts = [acc for acc in account_lookup.keys() 
                                if account_lookup[acc].get('account_type') == 'assets']
                has_asset = any(entry.get('account_code') in asset_accounts for entry in entries)
                
                if not has_asset:
                    compliance_issues.append("Revenue entry without corresponding asset or cash entry")
                    compliance_score -= 10
        
        # Matching principle - expenses should be matched with related revenues
        expense_accounts = [acc for acc in account_lookup.keys() 
                          if account_lookup[acc].get('account_type') == 'expenses']
        has_expense = any(entry.get('account_code') in expense_accounts for entry in entries)
        
        if has_expense and has_revenue:
            compliance_issues.append("Review: Expense and revenue in same entry - ensure proper matching")
        
        return {
            'compliance_score': compliance_score,
            'compliance_issues': compliance_issues,
            'has_cash_flow': has_cash_flow,
            'has_revenue': has_revenue,
            'has_expense': has_expense
        }
    
    def get_standard_chart_of_accounts(self) -> List[Dict[str, Any]]:
        """Get standard chart of accounts"""
        return [
            # Assets
            {'account_code': '1000', 'account_name': 'Cash and Cash Equivalents', 'account_type': 'assets'},
            {'account_code': '1020', 'account_name': 'Bank Account - Current', 'account_type': 'assets'},
            {'account_code': '1100', 'account_name': 'Accounts Receivable', 'account_type': 'assets'},
            {'account_code': '1110', 'account_name': 'Notes Receivable', 'account_type': 'assets'},
            {'account_code': '1200', 'account_name': 'Inventory', 'account_type': 'assets'},
            {'account_code': '1300', 'account_name': 'Prepaid Expenses', 'account_type': 'assets'},
            {'account_code': '1400', 'account_name': 'Fixed Assets', 'account_type': 'assets'},
            {'account_code': '1410', 'account_name': 'Equipment', 'account_type': 'assets'},
            {'account_code': '1420', 'account_name': 'Furniture & Fixtures', 'account_type': 'assets'},
            {'account_code': '1450', 'account_name': 'Accumulated Depreciation', 'account_type': 'assets'},
            
            # Liabilities
            {'account_code': '2000', 'account_name': 'Current Liabilities', 'account_type': 'liabilities'},
            {'account_code': '2010', 'account_name': 'Accounts Payable', 'account_type': 'liabilities'},
            {'account_code': '2020', 'account_name': 'Notes Payable', 'account_type': 'liabilities'},
            {'account_code': '2030', 'account_name': 'Accrued Expenses', 'account_type': 'liabilities'},
            {'account_code': '2100', 'account_name': 'Long-term Liabilities', 'account_type': 'liabilities'},
            {'account_code': '2110', 'account_name': 'Bank Loan', 'account_type': 'liabilities'},
            {'account_code': '2200', 'account_name': 'Tax Liabilities', 'account_type': 'liabilities'},
            {'account_code': '2210', 'account_name': 'GST Payable', 'account_type': 'liabilities'},
            
            # Equity
            {'account_code': '3000', 'account_name': 'Owner\'s Equity', 'account_type': 'equity'},
            {'account_code': '3010', 'account_name': 'Share Capital', 'account_type': 'equity'},
            {'account_code': '3020', 'account_name': 'Retained Earnings', 'account_type': 'equity'},
            {'account_code': '3030', 'account_name': 'Current Year Earnings', 'account_type': 'equity'},
            
            # Revenue
            {'account_code': '4000', 'account_name': 'Sales Revenue', 'account_type': 'revenue'},
            {'account_code': '4010', 'account_name': 'Product Sales', 'account_type': 'revenue'},
            {'account_code': '4020', 'account_name': 'Service Revenue', 'account_type': 'revenue'},
            {'account_code': '4100', 'account_name': 'Other Income', 'account_type': 'revenue'},
            {'account_code': '4110', 'account_name': 'Interest Income', 'account_type': 'revenue'},
            
            # Expenses
            {'account_code': '5000', 'account_name': 'Cost of Goods Sold', 'account_type': 'expenses'},
            {'account_code': '5100', 'account_name': 'Operating Expenses', 'account_type': 'expenses'},
            {'account_code': '5110', 'account_name': 'Salaries and Wages', 'account_type': 'expenses'},
            {'account_code': '5120', 'account_name': 'Rent Expense', 'account_type': 'expenses'},
            {'account_code': '5130', 'account_name': 'Utilities Expense', 'account_type': 'expenses'},
            {'account_code': '5140', 'account_name': 'Office Supplies', 'account_type': 'expenses'},
            {'account_code': '5150', 'account_name': 'Travel Expense', 'account_type': 'expenses'},
            {'account_code': '5200', 'account_name': 'Financial Expenses', 'account_type': 'expenses'},
            {'account_code': '5210', 'account_name': 'Interest Expense', 'account_type': 'expenses'},
            {'account_code': '5220', 'account_name': 'Bank Charges', 'account_type': 'expenses'},
            {'account_code': '5300', 'account_name': 'Depreciation Expense', 'account_type': 'expenses'}
        ]
    
    def create_journal_entry_with_review(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create journal entry with mandatory review process
        """
        try:
            # 1. Comprehensive validation
            validation_result = self.validate_journal_entry_comprehensive(entry_data)
            
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'message': 'Journal entry validation failed',
                    'validation_result': validation_result
                }
            
            # 2. Create draft journal entry
            entry_id = str(uuid.uuid4())
            
            journal_entry = ManualJournalEntry(
                entry_id=entry_id,
                entry_date=datetime.strptime(entry_data.get('date'), '%Y-%m-%d'),
                reference_number=entry_data.get('reference') or f"JE-{datetime.now().strftime('%Y%m%d')}-{entry_id[:8]}",
                description=entry_data.get('description', ''),
                debit_entries=[e for e in entry_data.get('entries', []) if float(e.get('debit_amount', 0)) > 0],
                credit_entries=[e for e in entry_data.get('entries', []) if float(e.get('credit_amount', 0)) > 0],
                total_debit=Decimal(str(validation_result['validation_details']['double_entry']['total_debits'])),
                total_credit=Decimal(str(validation_result['validation_details']['double_entry']['total_credits'])),
                status=JournalEntryStatus.PENDING_REVIEW,
                created_by=self.user_id,
                created_at=datetime.now(),
                notes=entry_data.get('notes', ''),
                attachments=entry_data.get('attachments', [])
            )
            
            # 3. Save to database (in real implementation)
            # journal_entry_record = self._save_to_database(journal_entry)
            
            return {
                'success': True,
                'message': 'Journal entry created and submitted for review',
                'entry_id': entry_id,
                'status': 'pending_review',
                'validation_result': validation_result,
                'journal_entry': {
                    'entry_id': journal_entry.entry_id,
                    'reference_number': journal_entry.reference_number,
                    'total_debit': float(journal_entry.total_debit),
                    'total_credit': float(journal_entry.total_credit),
                    'status': journal_entry.status.value,
                    'created_at': journal_entry.created_at.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating journal entry: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating journal entry: {str(e)}',
                'validation_result': None
            }
    
    def review_journal_entry(self, entry_id: str, reviewer_action: str, reviewer_notes: str = "") -> Dict[str, Any]:
        """
        Review journal entry - approve, reject, or request changes
        """
        try:
            # In real implementation, fetch from database
            # journal_entry = self._get_journal_entry_from_db(entry_id)
            
            reviewer_actions = ['approve', 'reject', 'request_changes']
            if reviewer_action not in reviewer_actions:
                return {
                    'success': False,
                    'message': f'Invalid reviewer action. Must be one of: {reviewer_actions}'
                }
            
            # Update entry status based on action
            if reviewer_action == 'approve':
                new_status = JournalEntryStatus.APPROVED
                message = 'Journal entry approved'
            elif reviewer_action == 'reject':
                new_status = JournalEntryStatus.REJECTED
                message = 'Journal entry rejected'
            else:  # request_changes
                new_status = JournalEntryStatus.DRAFT
                message = 'Changes requested for journal entry'
            
            # In real implementation, update database
            # self._update_journal_entry_status(entry_id, new_status, reviewer_notes)
            
            return {
                'success': True,
                'message': message,
                'entry_id': entry_id,
                'new_status': new_status.value,
                'reviewer_notes': reviewer_notes,
                'reviewed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error reviewing journal entry: {str(e)}")
            return {
                'success': False,
                'message': f'Error reviewing journal entry: {str(e)}'
            }
    
    def post_approved_journal_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        Post approved journal entry to ledger
        """
        try:
            # In real implementation, fetch approved entry from database
            # journal_entry = self._get_approved_journal_entry(entry_id)
            
            # Validate entry is approved
            # if journal_entry.status != JournalEntryStatus.APPROVED:
            #     return {'success': False, 'message': 'Entry must be approved before posting'}
            
            # Post to ledger through accounting engine
            # posting_result = self.accounting_engine.post_manual_journal_entry(journal_entry)
            
            # Update status to posted
            # self._update_journal_entry_status(entry_id, JournalEntryStatus.POSTED)
            
            return {
                'success': True,
                'message': 'Journal entry posted to ledger successfully',
                'entry_id': entry_id,
                'posted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error posting journal entry: {str(e)}")
            return {
                'success': False,
                'message': f'Error posting journal entry: {str(e)}'
            }
        
    def get_ledger_accounts(self) -> List[Dict[str, Any]]:
        """Get all available ledger accounts from ledger report"""
        try:
            # Get ledger report from accounting engine
            ledger_report = self.accounting_engine.generate_ledger_report()
            
            # Extract unique accounts from ledger report
            ledger_accounts = []
            
            if ledger_report and 'ledger_accounts' in ledger_report:
                for account in ledger_report['ledger_accounts']:
                    ledger_accounts.append({
                        'account_code': account.get('account_code', ''),
                        'account_name': account.get('account_name', ''),
                        'account_type': account.get('account_type', ''),
                        'current_balance': account.get('closing_balance', 0),
                        'description': account.get('description', ''),
                        'is_active': True
                    })
            
            # Add standard chart of accounts if ledger is empty
            if not ledger_accounts:
                ledger_accounts = self._get_standard_ledger_accounts()
            
            return sorted(ledger_accounts, key=lambda x: x['account_code'])
            
        except Exception as e:
            logger.error(f"Error getting ledger accounts: {str(e)}")
            return self._get_standard_ledger_accounts()
    
    def _get_standard_ledger_accounts(self) -> List[Dict[str, Any]]:
        """Get standard chart of accounts"""
        return [
            {'account_code': '1000', 'account_name': 'Cash and Cash Equivalents', 'account_type': 'assets', 'current_balance': 0, 'description': 'Cash on hand and in bank accounts', 'is_active': True},
            {'account_code': '1010', 'account_name': 'Petty Cash', 'account_type': 'assets', 'current_balance': 0, 'description': 'Small cash fund for minor expenses', 'is_active': True},
            {'account_code': '1020', 'account_name': 'Bank Account - Current', 'account_type': 'assets', 'current_balance': 0, 'description': 'Current account with bank', 'is_active': True},
            {'account_code': '1100', 'account_name': 'Accounts Receivable', 'account_type': 'assets', 'current_balance': 0, 'description': 'Money owed by customers', 'is_active': True},
            {'account_code': '1200', 'account_name': 'Inventory', 'account_type': 'assets', 'current_balance': 0, 'description': 'Goods held for sale', 'is_active': True},
            {'account_code': '1500', 'account_name': 'Fixed Assets', 'account_type': 'assets', 'current_balance': 0, 'description': 'Long-term assets', 'is_active': True},
            {'account_code': '2000', 'account_name': 'Accounts Payable', 'account_type': 'liabilities', 'current_balance': 0, 'description': 'Money owed to suppliers', 'is_active': True},
            {'account_code': '2100', 'account_name': 'Accrued Expenses', 'account_type': 'liabilities', 'current_balance': 0, 'description': 'Expenses incurred but not yet paid', 'is_active': True},
            {'account_code': '2500', 'account_name': 'Long-term Debt', 'account_type': 'liabilities', 'current_balance': 0, 'description': 'Long-term loans and debt', 'is_active': True},
            {'account_code': '3000', 'account_name': 'Share Capital', 'account_type': 'equity', 'current_balance': 0, 'description': 'Owner\'s equity in the business', 'is_active': True},
            {'account_code': '3100', 'account_name': 'Retained Earnings', 'account_type': 'equity', 'current_balance': 0, 'description': 'Accumulated profits', 'is_active': True},
            {'account_code': '4000', 'account_name': 'Sales Revenue', 'account_type': 'revenue', 'current_balance': 0, 'description': 'Revenue from sales', 'is_active': True},
            {'account_code': '4100', 'account_name': 'Service Revenue', 'account_type': 'revenue', 'current_balance': 0, 'description': 'Revenue from services', 'is_active': True},
            {'account_code': '5000', 'account_name': 'Cost of Goods Sold', 'account_type': 'expenses', 'current_balance': 0, 'description': 'Direct costs of goods sold', 'is_active': True},
            {'account_code': '6000', 'account_name': 'Operating Expenses', 'account_type': 'expenses', 'current_balance': 0, 'description': 'General operating expenses', 'is_active': True},
            {'account_code': '6100', 'account_name': 'Salaries and Wages', 'account_type': 'expenses', 'current_balance': 0, 'description': 'Employee compensation', 'is_active': True},
            {'account_code': '6200', 'account_name': 'Rent Expense', 'account_type': 'expenses', 'current_balance': 0, 'description': 'Office and facility rent', 'is_active': True},
            {'account_code': '6300', 'account_name': 'Utilities', 'account_type': 'expenses', 'current_balance': 0, 'description': 'Electricity, water, gas', 'is_active': True},
            {'account_code': '6400', 'account_name': 'Office Supplies', 'account_type': 'expenses', 'current_balance': 0, 'description': 'Stationery and office materials', 'is_active': True},
            {'account_code': '6500', 'account_name': 'Professional Fees', 'account_type': 'expenses', 'current_balance': 0, 'description': 'Legal and accounting fees', 'is_active': True}
        ]
    
    def create_ledger_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ledger account"""
        try:
            # Validate account data
            required_fields = ['account_code', 'account_name', 'account_type']
            for field in required_fields:
                if field not in account_data or not account_data[field]:
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Check if account code already exists
            existing_accounts = self.get_ledger_accounts()
            if any(acc['account_code'] == account_data['account_code'] for acc in existing_accounts):
                return {'success': False, 'error': 'Account code already exists'}
            
            # Create new account
            new_account = LedgerAccount(
                account_code=account_data['account_code'],
                account_name=account_data['account_name'],
                account_type=LedgerAccountType(account_data['account_type']),
                parent_account=account_data.get('parent_account'),
                description=account_data.get('description', ''),
                is_active=True,
                created_by=self.user_id,
                created_at=datetime.utcnow(),
                opening_balance=Decimal(str(account_data.get('opening_balance', 0)))
            )
            
            # Store in database (you would implement actual database storage here)
            # For now, we'll return success
            
            return {
                'success': True,
                'account': {
                    'account_code': new_account.account_code,
                    'account_name': new_account.account_name,
                    'account_type': new_account.account_type.value,
                    'description': new_account.description,
                    'opening_balance': float(new_account.opening_balance),
                    'is_active': new_account.is_active
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating ledger account: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_manual_journal_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new manual journal entry"""
        try:
            # Validate entry data
            if not entry_data.get('entries') or len(entry_data['entries']) < 2:
                return {'success': False, 'error': 'At least two entries required for a journal entry'}
            
            # Calculate totals
            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')
            debit_entries = []
            credit_entries = []
            
            for entry in entry_data['entries']:
                debit_amount = Decimal(str(entry.get('debit_amount', 0)))
                credit_amount = Decimal(str(entry.get('credit_amount', 0)))
                
                total_debit += debit_amount
                total_credit += credit_amount
                
                if debit_amount > 0:
                    debit_entries.append({
                        'account_code': entry['account_code'],
                        'account_name': entry['account_name'],
                        'amount': float(debit_amount),
                        'description': entry.get('description', '')
                    })
                
                if credit_amount > 0:
                    credit_entries.append({
                        'account_code': entry['account_code'],
                        'account_name': entry['account_name'],
                        'amount': float(credit_amount),
                        'description': entry.get('description', '')
                    })
            
            # Validate double-entry
            if total_debit != total_credit:
                return {'success': False, 'error': f'Debits (₹{total_debit}) must equal Credits (₹{total_credit})'}
            
            # Create journal entry
            journal_entry = ManualJournalEntry(
                entry_id=str(uuid.uuid4()),
                entry_date=datetime.strptime(entry_data['entry_date'], '%Y-%m-%d'),
                reference_number=entry_data.get('reference_number', f"MJE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
                description=entry_data['description'],
                debit_entries=debit_entries,
                credit_entries=credit_entries,
                total_debit=total_debit,
                total_credit=total_credit,
                status=JournalEntryStatus.DRAFT,
                created_by=self.user_id,
                created_at=datetime.utcnow(),
                notes=entry_data.get('notes', '')
            )
            
            # Store in session for review (in a real application, store in database)
            
            return {
                'success': True,
                'entry': {
                    'entry_id': journal_entry.entry_id,
                    'entry_date': journal_entry.entry_date.strftime('%Y-%m-%d'),
                    'reference_number': journal_entry.reference_number,
                    'description': journal_entry.description,
                    'debit_entries': journal_entry.debit_entries,
                    'credit_entries': journal_entry.credit_entries,
                    'total_debit': float(journal_entry.total_debit),
                    'total_credit': float(journal_entry.total_credit),
                    'status': journal_entry.status.value,
                    'created_at': journal_entry.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating manual journal entry: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_pending_journal_entries(self) -> List[Dict[str, Any]]:
        """Get all pending journal entries for review"""
        try:
            # In a real application, fetch from database
            # For now, return mock data
            pending_entries = [
                {
                    'entry_id': 'MJE-001',
                    'entry_date': '2025-01-06',
                    'reference_number': 'MJE-20250106-001',
                    'description': 'Office rent payment for January 2025',
                    'total_debit': 25000.00,
                    'total_credit': 25000.00,
                    'status': 'pending_review',
                    'created_by': 'John Doe',
                    'created_at': '2025-01-06 10:30:00',
                    'debit_entries': [
                        {'account_code': '6200', 'account_name': 'Rent Expense', 'amount': 25000.00, 'description': 'Office rent - January 2025'}
                    ],
                    'credit_entries': [
                        {'account_code': '1020', 'account_name': 'Bank Account - Current', 'amount': 25000.00, 'description': 'Payment via bank transfer'}
                    ]
                }
            ]
            
            return pending_entries
            
        except Exception as e:
            logger.error(f"Error getting pending journal entries: {str(e)}")
            return []
    
    def approve_journal_entry(self, entry_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a journal entry"""
        try:
            # In a real application, update database
            # For now, return success
            
            return {
                'success': True,
                'entry_id': entry_id,
                'status': 'approved',
                'approved_by': self.user_id,
                'approved_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'notes': approval_data.get('notes', '')
            }
            
        except Exception as e:
            logger.error(f"Error approving journal entry: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def post_journal_entry(self, entry_id: str) -> Dict[str, Any]:
        """Post approved journal entry and update all reports"""
        try:
            # In a real application, this would:
            # 1. Post the entry to the general ledger
            # 2. Update account balances
            # 3. Trigger report regeneration
            
            # For now, simulate the process
            result = {
                'success': True,
                'entry_id': entry_id,
                'status': 'posted',
                'posted_by': self.user_id,
                'posted_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_reports': [
                    'journal_report',
                    'ledger_report',
                    'trial_balance',
                    'profit_loss_statement',
                    'balance_sheet',
                    'cash_flow_statement'
                ]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error posting journal entry: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_account_suggestions(self, search_term: str) -> List[Dict[str, Any]]:
        """Get account suggestions based on search term"""
        try:
            accounts = self.get_ledger_accounts()
            suggestions = []
            
            search_term = search_term.lower()
            
            for account in accounts:
                if (search_term in account['account_code'].lower() or 
                    search_term in account['account_name'].lower() or
                    search_term in account.get('description', '').lower()):
                    suggestions.append({
                        'account_code': account['account_code'],
                        'account_name': account['account_name'],
                        'account_type': account['account_type'],
                        'current_balance': account['current_balance'],
                        'display_text': f"{account['account_code']} - {account['account_name']}"
                    })
            
            return suggestions[:10]  # Return top 10 matches
            
        except Exception as e:
            logger.error(f"Error getting account suggestions: {str(e)}")
            return []
    
    def validate_journal_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate journal entry with comprehensive accounting rules"""
        try:
            validation_results = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'accounting_analysis': {}
            }
            
            # Check required fields
            if not entry_data.get('description'):
                validation_results['errors'].append('Description is required')
                validation_results['is_valid'] = False
            
            if not entry_data.get('entry_date'):
                validation_results['errors'].append('Entry date is required')
                validation_results['is_valid'] = False
            
            entries = entry_data.get('entries', [])
            if len(entries) < 2:
                validation_results['errors'].append('At least two entries required for double-entry bookkeeping')
                validation_results['is_valid'] = False
                return validation_results
            
            # Get ledger accounts for validation
            ledger_accounts = {acc['account_code']: acc for acc in self.get_ledger_accounts()}
            
            # Validate each entry
            total_debit = Decimal('0')
            total_credit = Decimal('0')
            debit_entries = []
            credit_entries = []
            
            for i, entry in enumerate(entries):
                account_code = entry.get('account_code')
                debit_amount = Decimal(str(entry.get('debit_amount', 0)))
                credit_amount = Decimal(str(entry.get('credit_amount', 0)))
                
                # Validate account exists
                if account_code not in ledger_accounts:
                    validation_results['errors'].append(f'Entry {i+1}: Account code {account_code} not found')
                    validation_results['is_valid'] = False
                    continue
                
                account = ledger_accounts[account_code]
                account_type = account['account_type'].lower()
                
                # Validate amounts
                if debit_amount < 0:
                    validation_results['errors'].append(f'Entry {i+1}: Debit amount cannot be negative')
                    validation_results['is_valid'] = False
                
                if credit_amount < 0:
                    validation_results['errors'].append(f'Entry {i+1}: Credit amount cannot be negative')
                    validation_results['is_valid'] = False
                
                # Validate only one side (debit OR credit) is entered
                if debit_amount > 0 and credit_amount > 0:
                    validation_results['errors'].append(f'Entry {i+1}: Cannot have both debit and credit amounts')
                    validation_results['is_valid'] = False
                
                if debit_amount == 0 and credit_amount == 0:
                    validation_results['errors'].append(f'Entry {i+1}: Must enter either debit or credit amount')
                    validation_results['is_valid'] = False
                
                # Apply accounting rules validation
                if debit_amount > 0:
                    total_debit += debit_amount
                    debit_entries.append({
                        'account_code': account_code,
                        'account_name': account['account_name'],
                        'account_type': account_type,
                        'amount': debit_amount,
                        'description': entry.get('description', '')
                    })
                    
                    # Validate debit accounting rules
                    self._validate_debit_rules(account_type, account, debit_amount, validation_results, i+1)
                
                elif credit_amount > 0:
                    total_credit += credit_amount
                    credit_entries.append({
                        'account_code': account_code,
                        'account_name': account['account_name'],
                        'account_type': account_type,
                        'amount': credit_amount,
                        'description': entry.get('description', '')
                    })
                    
                    # Validate credit accounting rules
                    self._validate_credit_rules(account_type, account, credit_amount, validation_results, i+1)
            
            # Fundamental double-entry validation
            if total_debit != total_credit:
                validation_results['errors'].append(
                    f'Double-entry rule violation: Total debits (₹{total_debit}) must equal total credits (₹{total_credit}). '
                    f'Difference: ₹{abs(total_debit - total_credit)}'
                )
                validation_results['is_valid'] = False
            
            # Validate transaction logic
            self._validate_transaction_logic(debit_entries, credit_entries, validation_results)
            
            # Add accounting analysis
            validation_results['accounting_analysis'] = {
                'total_amount': str(total_debit),
                'debit_entries_count': len(debit_entries),
                'credit_entries_count': len(credit_entries),
                'affected_account_types': list(set([entry['account_type'] for entry in debit_entries + credit_entries])),
                'transaction_summary': self._generate_transaction_summary(debit_entries, credit_entries)
            }
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating journal entry: {str(e)}")
            return {'is_valid': False, 'errors': [str(e)], 'warnings': [], 'accounting_analysis': {}}
    
    def _validate_debit_rules(self, account_type: str, account: Dict, amount: Decimal, validation_results: Dict, entry_num: int):
        """Validate accounting rules for debit entries"""
        # Debit increases: Assets, Expenses, Dividends, Losses
        # Debit decreases: Liabilities, Equity, Revenue
        
        if account_type in ['assets', 'asset']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Debiting {account["account_name"]} (Asset) increases the asset balance'
            )
        elif account_type in ['expenses', 'expense']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Debiting {account["account_name"]} (Expense) records an expense transaction'
            )
        elif account_type in ['liabilities', 'liability']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Debiting {account["account_name"]} (Liability) decreases the liability balance'
            )
        elif account_type in ['equity', 'capital']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Debiting {account["account_name"]} (Equity) decreases owner\'s equity'
            )
        elif account_type in ['revenue', 'income']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Debiting {account["account_name"]} (Revenue) reduces revenue (unusual - verify)'
            )
    
    def _validate_credit_rules(self, account_type: str, account: Dict, amount: Decimal, validation_results: Dict, entry_num: int):
        """Validate accounting rules for credit entries"""
        # Credit increases: Liabilities, Equity, Revenue
        # Credit decreases: Assets, Expenses
        
        if account_type in ['liabilities', 'liability']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Crediting {account["account_name"]} (Liability) increases the liability balance'
            )
        elif account_type in ['equity', 'capital']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Crediting {account["account_name"]} (Equity) increases owner\'s equity'
            )
        elif account_type in ['revenue', 'income']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Crediting {account["account_name"]} (Revenue) records revenue earned'
            )
        elif account_type in ['assets', 'asset']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Crediting {account["account_name"]} (Asset) decreases the asset balance'
            )
        elif account_type in ['expenses', 'expense']:
            validation_results['warnings'].append(
                f'Entry {entry_num}: Crediting {account["account_name"]} (Expense) reduces expense (unusual - verify)'
            )
    
    def _validate_transaction_logic(self, debit_entries: List[Dict], credit_entries: List[Dict], validation_results: Dict):
        """Validate overall transaction logic"""
        
        # Common transaction patterns validation
        debit_types = [entry['account_type'] for entry in debit_entries]
        credit_types = [entry['account_type'] for entry in credit_entries]
        
        # Check for logical transaction patterns
        if 'assets' in debit_types and 'revenue' in credit_types:
            validation_results['warnings'].append('Transaction Pattern: Revenue recognition (Asset increase, Revenue increase)')
        
        elif 'expenses' in debit_types and 'assets' in credit_types:
            validation_results['warnings'].append('Transaction Pattern: Expense payment (Expense increase, Asset decrease)')
        
        elif 'assets' in debit_types and 'liabilities' in credit_types:
            validation_results['warnings'].append('Transaction Pattern: Asset acquisition on credit (Asset increase, Liability increase)')
        
        elif 'liabilities' in debit_types and 'assets' in credit_types:
            validation_results['warnings'].append('Transaction Pattern: Liability payment (Liability decrease, Asset decrease)')
        
        elif 'assets' in debit_types and 'equity' in credit_types:
            validation_results['warnings'].append('Transaction Pattern: Owner investment (Asset increase, Equity increase)')
        
        # Validate that transaction makes business sense
        if len(set(debit_types + credit_types)) == 1:
            validation_results['errors'].append('Invalid transaction: All entries are of the same account type')
            validation_results['is_valid'] = False
    
    def _generate_transaction_summary(self, debit_entries: List[Dict], credit_entries: List[Dict]) -> str:
        """Generate human-readable transaction summary"""
        
        if not debit_entries or not credit_entries:
            return "Incomplete transaction"
        
        # Simplify for single debit, single credit
        if len(debit_entries) == 1 and len(credit_entries) == 1:
            debit = debit_entries[0]
            credit = credit_entries[0]
            
            return f"₹{debit['amount']} transfer from {credit['account_name']} to {debit['account_name']}"
        
        # Multiple entries summary
        total_amount = sum(entry['amount'] for entry in debit_entries)
        debit_accounts = [entry['account_name'] for entry in debit_entries]
        credit_accounts = [entry['account_name'] for entry in credit_entries]
        
        return f"₹{total_amount} transaction affecting {len(debit_entries)} debit accounts ({', '.join(debit_accounts[:2])}) and {len(credit_entries)} credit accounts ({', '.join(credit_accounts[:2])})"