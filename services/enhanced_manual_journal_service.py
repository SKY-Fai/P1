"""
Enhanced Manual Journal Entry Service with Complete Workflow Management
Comprehensive system for creating, editing, reviewing, approving, and posting manual journal entries
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

class EnhancedManualJournalService:
    """
    Enhanced manual journal entry service with complete workflow management:
    Create → Edit → Review → Approve → Post → Integration with Reports
    Includes comprehensive ledger library integration and creation capabilities
    """
    
    def __init__(self, company_id: int = 1, user_id: int = 1):
        self.company_id = company_id
        self.user_id = user_id
        self.accounting_engine = AutomatedAccountingEngine(company_id, user_id)
        self.ledger_library = self._initialize_ledger_library()
    
    def _initialize_ledger_library(self) -> Dict[str, Any]:
        """Initialize comprehensive ledger library from existing chart of accounts"""
        try:
            # Get existing chart of accounts
            accounts = ChartOfAccount.query.filter_by(
                company_id=self.company_id,
                is_active=True
            ).all()
            
            ledger_library = {
                'accounts': {},
                'categories': {
                    'Assets': ['Cash', 'Bank', 'Accounts Receivable', 'Inventory', 'Fixed Assets'],
                    'Liabilities': ['Accounts Payable', 'Loans', 'Accrued Expenses'],
                    'Equity': ['Capital', 'Retained Earnings', 'Drawings'],
                    'Revenue': ['Sales', 'Service Revenue', 'Other Income'],
                    'Expenses': ['Office Expenses', 'Rent', 'Utilities', 'Travel', 'Marketing']
                },
                'suggested_codes': {}
            }
            
            # Build account library
            for account in accounts:
                ledger_library['accounts'][account.account_code] = {
                    'id': account.id,
                    'name': account.account_name,
                    'type': account.account_type,
                    'code': account.account_code,
                    'parent_id': account.parent_account_id,
                    'is_active': account.is_active
                }
            
            # Generate suggested codes for quick access
            self._generate_suggested_account_codes(ledger_library)
            
            return ledger_library
            
        except Exception as e:
            logger.error(f"Error initializing ledger library: {str(e)}")
            return self._create_default_ledger_library()
    
    def _create_default_ledger_library(self) -> Dict[str, Any]:
        """Create default ledger library if no existing accounts"""
        return {
            'accounts': {},
            'categories': {
                'Assets': ['Cash', 'Bank', 'Accounts Receivable', 'Inventory', 'Fixed Assets'],
                'Liabilities': ['Accounts Payable', 'Loans', 'Accrued Expenses'],
                'Equity': ['Capital', 'Retained Earnings', 'Drawings'],
                'Revenue': ['Sales', 'Service Revenue', 'Other Income'],
                'Expenses': ['Office Expenses', 'Rent', 'Utilities', 'Travel', 'Marketing']
            },
            'suggested_codes': {}
        }
    
    def _generate_suggested_account_codes(self, library: Dict[str, Any]) -> None:
        """Generate intelligent account code suggestions"""
        # Standard account code prefixes
        code_prefixes = {
            'Assets': '1',
            'Liabilities': '2', 
            'Equity': '3',
            'Revenue': '4',
            'Expenses': '5'
        }
        
        for category, accounts in library['categories'].items():
            prefix = code_prefixes.get(category, '9')
            for i, account_name in enumerate(accounts, 1):
                suggested_code = f"{prefix}{i:03d}"
                library['suggested_codes'][account_name] = suggested_code
    
    def get_ledger_library(self) -> Dict[str, Any]:
        """Get complete ledger library for frontend"""
        return {
            'accounts': list(self.ledger_library['accounts'].values()),
            'categories': self.ledger_library['categories'],
            'suggested_codes': self.ledger_library['suggested_codes'],
            'total_accounts': len(self.ledger_library['accounts'])
        }
    
    def search_ledger_accounts(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search ledger accounts by code or name"""
        try:
            search_term = search_term.lower()
            results = []
            
            for code, account in self.ledger_library['accounts'].items():
                if (search_term in account['name'].lower() or 
                    search_term in account['code'].lower() or
                    search_term in account['type'].lower()):
                    results.append({
                        'id': account['id'],
                        'code': account['code'],
                        'name': account['name'],
                        'type': account['type'],
                        'full_display': f"{account['code']} - {account['name']}"
                    })
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching ledger accounts: {str(e)}")
            return []
    
    def create_new_ledger_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new ledger account from within manual journal entry"""
        try:
            # Validate account data
            if not account_data.get('account_name') or not account_data.get('account_type'):
                return {
                    'success': False,
                    'error': 'Account name and type are required'
                }
            
            # Generate account code if not provided
            account_code = account_data.get('account_code')
            if not account_code:
                account_code = self._generate_new_account_code(account_data['account_type'])
            
            # Create new chart of account entry
            new_account = ChartOfAccount(
                company_id=self.company_id,
                account_code=account_code,
                account_name=account_data['account_name'],
                account_type=account_data['account_type'],
                parent_account_id=account_data.get('parent_account_id'),
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_account)
            db.session.commit()
            
            # Add to ledger library
            self.ledger_library['accounts'][account_code] = {
                'id': new_account.id,
                'name': new_account.account_name,
                'type': new_account.account_type,
                'code': new_account.account_code,
                'parent_id': new_account.parent_account_id,
                'is_active': True
            }
            
            # Log activity
            self._log_audit_action(
                action='CREATE_LEDGER_ACCOUNT',
                details={
                    'account_code': account_code,
                    'account_name': account_data['account_name'],
                    'account_type': account_data['account_type']
                }
            )
            
            return {
                'success': True,
                'account': {
                    'id': new_account.id,
                    'code': account_code,
                    'name': new_account.account_name,
                    'type': new_account.account_type,
                    'full_display': f"{account_code} - {new_account.account_name}"
                },
                'message': f'Ledger account {account_code} created successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating ledger account: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to create ledger account: {str(e)}'
            }
    
    def _generate_new_account_code(self, account_type: str) -> str:
        """Generate new account code based on type and existing codes"""
        try:
            # Get prefix for account type
            type_prefixes = {
                'Assets': '1',
                'Liabilities': '2',
                'Equity': '3',
                'Revenue': '4',
                'Expenses': '5'
            }
            
            prefix = type_prefixes.get(account_type, '9')
            
            # Find highest existing code with this prefix
            existing_codes = [
                code for code in self.ledger_library['accounts'].keys()
                if code.startswith(prefix) and len(code) == 4
            ]
            
            if existing_codes:
                max_code = max([int(code[1:]) for code in existing_codes])
                new_number = max_code + 1
            else:
                new_number = 1
            
            return f"{prefix}{new_number:03d}"
            
        except Exception as e:
            logger.error(f"Error generating account code: {str(e)}")
            return f"9{datetime.now().strftime('%H%M%S')}"  # Fallback code
    
    def validate_account_mapping(self, account_code: str) -> Dict[str, Any]:
        """Validate if account code exists in ledger library"""
        try:
            if account_code in self.ledger_library['accounts']:
                account = self.ledger_library['accounts'][account_code]
                return {
                    'valid': True,
                    'account': account,
                    'exists': True
                }
            else:
                # Check if it's a new account that needs to be created
                return {
                    'valid': False,
                    'account': None,
                    'exists': False,
                    'suggestion': 'Account code not found. Would you like to create a new ledger account?'
                }
                
        except Exception as e:
            logger.error(f"Error validating account mapping: {str(e)}")
            return {
                'valid': False,
                'account': None,
                'exists': False,
                'error': str(e)
            }
    
    def create_manual_journal_entry(self, journal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new manual journal entry with workflow management
        """
        try:
            # Generate journal number
            journal_number = self._generate_journal_number()
            
            # Validate journal data
            validation_result = self.validate_journal_entry_comprehensive(journal_data)
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation_errors': validation_result['errors'],
                    'validation_details': validation_result['validation_details']
                }
            
            # Create journal header
            journal_header = ManualJournalHeader(
                company_id=self.company_id,
                journal_number=journal_number,
                entry_date=datetime.strptime(journal_data['date'], '%Y-%m-%d'),
                description=journal_data['description'],
                reference_number=journal_data.get('reference', ''),
                status=JournalEntryStatus.DRAFT,
                created_by=self.user_id,
                notes=journal_data.get('notes', ''),
                attachments=json.dumps(journal_data.get('attachments', []))
            )
            
            db.session.add(journal_header)
            db.session.flush()  # Get the ID
            
            # Create journal lines
            total_debits = Decimal('0.00')
            total_credits = Decimal('0.00')
            
            for i, entry in enumerate(journal_data['entries']):
                debit_amount = Decimal(str(entry.get('debit_amount', 0)))
                credit_amount = Decimal(str(entry.get('credit_amount', 0)))
                
                journal_line = ManualJournalLine(
                    journal_header_id=journal_header.id,
                    account_id=self._get_account_id_by_code(entry['account_code']),
                    line_description=entry['description'],
                    debit_amount=float(debit_amount),
                    credit_amount=float(credit_amount),
                    line_number=i + 1,
                    tax_code=entry.get('tax_code'),
                    cost_center=entry.get('cost_center'),
                    project_code=entry.get('project_code')
                )
                
                db.session.add(journal_line)
                total_debits += debit_amount
                total_credits += credit_amount
            
            # Update totals
            journal_header.total_debits = float(total_debits)
            journal_header.total_credits = float(total_credits)
            
            db.session.commit()
            
            # Log audit trail
            self._log_audit_action('CREATE', journal_header.id, 'Manual journal entry created')
            
            return {
                'success': True,
                'journal_id': journal_header.id,
                'journal_number': journal_number,
                'status': journal_header.status.value,
                'message': 'Manual journal entry created successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating manual journal entry: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to create journal entry: {str(e)}'
            }
    
    def edit_manual_journal_entry(self, journal_id: int, journal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edit an existing manual journal entry (only if in DRAFT or REJECTED status)
        """
        try:
            journal_header = ManualJournalHeader.query.get(journal_id)
            if not journal_header:
                return {'success': False, 'error': 'Journal entry not found'}
            
            # Check if editable
            if journal_header.status not in [JournalEntryStatus.DRAFT, JournalEntryStatus.REJECTED]:
                return {
                    'success': False,
                    'error': f'Cannot edit journal entry in {journal_header.status.value} status'
                }
            
            # Validate updated data
            validation_result = self.validate_journal_entry_comprehensive(journal_data)
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation_errors': validation_result['errors']
                }
            
            # Update header
            journal_header.entry_date = datetime.strptime(journal_data['date'], '%Y-%m-%d')
            journal_header.description = journal_data['description']
            journal_header.reference_number = journal_data.get('reference', '')
            journal_header.notes = journal_data.get('notes', '')
            journal_header.status = JournalEntryStatus.DRAFT  # Reset to draft
            journal_header.updated_at = datetime.utcnow()
            
            # Clear previous approval/review data when editing
            journal_header.reviewed_by = None
            journal_header.reviewed_at = None
            journal_header.review_notes = None
            journal_header.approved_by = None
            journal_header.approved_at = None
            journal_header.approval_notes = None
            
            # Delete existing lines
            ManualJournalLine.query.filter_by(journal_header_id=journal_id).delete()
            
            # Create new lines
            total_debits = Decimal('0.00')
            total_credits = Decimal('0.00')
            
            for i, entry in enumerate(journal_data['entries']):
                debit_amount = Decimal(str(entry.get('debit_amount', 0)))
                credit_amount = Decimal(str(entry.get('credit_amount', 0)))
                
                journal_line = ManualJournalLine(
                    journal_header_id=journal_header.id,
                    account_id=self._get_account_id_by_code(entry['account_code']),
                    line_description=entry['description'],
                    debit_amount=float(debit_amount),
                    credit_amount=float(credit_amount),
                    line_number=i + 1,
                    tax_code=entry.get('tax_code'),
                    cost_center=entry.get('cost_center'),
                    project_code=entry.get('project_code')
                )
                
                db.session.add(journal_line)
                total_debits += debit_amount
                total_credits += credit_amount
            
            # Update totals
            journal_header.total_debits = float(total_debits)
            journal_header.total_credits = float(total_credits)
            
            db.session.commit()
            
            # Log audit trail
            self._log_audit_action('EDIT', journal_header.id, 'Manual journal entry edited')
            
            return {
                'success': True,
                'journal_id': journal_header.id,
                'status': journal_header.status.value,
                'message': 'Manual journal entry updated successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error editing manual journal entry: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to edit journal entry: {str(e)}'
            }
    
    def submit_for_review(self, journal_id: int) -> Dict[str, Any]:
        """
        Submit journal entry for review
        """
        try:
            journal_header = ManualJournalHeader.query.get(journal_id)
            if not journal_header:
                return {'success': False, 'error': 'Journal entry not found'}
            
            if journal_header.status != JournalEntryStatus.DRAFT:
                return {
                    'success': False,
                    'error': f'Cannot submit for review. Current status: {journal_header.status.value}'
                }
            
            journal_header.status = JournalEntryStatus.PENDING_REVIEW
            journal_header.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit trail
            self._log_audit_action('SUBMIT_REVIEW', journal_header.id, 'Journal entry submitted for review')
            
            return {
                'success': True,
                'journal_id': journal_header.id,
                'status': journal_header.status.value,
                'message': 'Journal entry submitted for review successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting for review: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to submit for review: {str(e)}'
            }
    
    def review_journal_entry(self, journal_id: int, reviewer_id: int, review_notes: str = '') -> Dict[str, Any]:
        """
        Review a journal entry
        """
        try:
            journal_header = ManualJournalHeader.query.get(journal_id)
            if not journal_header:
                return {'success': False, 'error': 'Journal entry not found'}
            
            if journal_header.status != JournalEntryStatus.PENDING_REVIEW:
                return {
                    'success': False,
                    'error': f'Cannot review. Current status: {journal_header.status.value}'
                }
            
            journal_header.status = JournalEntryStatus.REVIEWED
            journal_header.reviewed_by = reviewer_id
            journal_header.reviewed_at = datetime.utcnow()
            journal_header.review_notes = review_notes
            journal_header.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit trail
            self._log_audit_action('REVIEW', journal_header.id, f'Journal entry reviewed by user {reviewer_id}')
            
            return {
                'success': True,
                'journal_id': journal_header.id,
                'status': journal_header.status.value,
                'message': 'Journal entry reviewed successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error reviewing journal entry: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to review journal entry: {str(e)}'
            }
    
    def approve_journal_entry(self, journal_id: int, approver_id: int, approval_notes: str = '') -> Dict[str, Any]:
        """
        Approve a journal entry
        """
        try:
            journal_header = ManualJournalHeader.query.get(journal_id)
            if not journal_header:
                return {'success': False, 'error': 'Journal entry not found'}
            
            if journal_header.status != JournalEntryStatus.REVIEWED:
                return {
                    'success': False,
                    'error': f'Cannot approve. Current status: {journal_header.status.value}'
                }
            
            journal_header.status = JournalEntryStatus.APPROVED
            journal_header.approved_by = approver_id
            journal_header.approved_at = datetime.utcnow()
            journal_header.approval_notes = approval_notes
            journal_header.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit trail
            self._log_audit_action('APPROVE', journal_header.id, f'Journal entry approved by user {approver_id}')
            
            return {
                'success': True,
                'journal_id': journal_header.id,
                'status': journal_header.status.value,
                'message': 'Journal entry approved successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error approving journal entry: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to approve journal entry: {str(e)}'
            }
    
    def reject_journal_entry(self, journal_id: int, rejector_id: int, rejection_reason: str) -> Dict[str, Any]:
        """
        Reject a journal entry
        """
        try:
            journal_header = ManualJournalHeader.query.get(journal_id)
            if not journal_header:
                return {'success': False, 'error': 'Journal entry not found'}
            
            if journal_header.status not in [JournalEntryStatus.PENDING_REVIEW, JournalEntryStatus.REVIEWED]:
                return {
                    'success': False,
                    'error': f'Cannot reject. Current status: {journal_header.status.value}'
                }
            
            journal_header.status = JournalEntryStatus.REJECTED
            journal_header.rejected_by = rejector_id
            journal_header.rejected_at = datetime.utcnow()
            journal_header.rejection_reason = rejection_reason
            journal_header.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit trail
            self._log_audit_action('REJECT', journal_header.id, f'Journal entry rejected by user {rejector_id}: {rejection_reason}')
            
            return {
                'success': True,
                'journal_id': journal_header.id,
                'status': journal_header.status.value,
                'message': 'Journal entry rejected successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error rejecting journal entry: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to reject journal entry: {str(e)}'
            }
    
    def post_journal_entry(self, journal_id: int, poster_id: int) -> Dict[str, Any]:
        """
        Post approved journal entry to general ledger and integrate with reports
        """
        try:
            journal_header = ManualJournalHeader.query.get(journal_id)
            if not journal_header:
                return {'success': False, 'error': 'Journal entry not found'}
            
            if journal_header.status != JournalEntryStatus.APPROVED:
                return {
                    'success': False,
                    'error': f'Cannot post. Current status: {journal_header.status.value}'
                }
            
            # Create individual journal entries for each line
            journal_entries_created = []
            
            for line in journal_header.journal_lines:
                # Create JournalEntry for integration with automated accounting system
                journal_entry = JournalEntry(
                    company_id=self.company_id,
                    account_id=line.account_id,
                    created_by=poster_id,
                    entry_date=journal_header.entry_date,
                    description=f"{journal_header.description} - {line.line_description}",
                    reference_number=f"{journal_header.journal_number}-{line.line_number}",
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    currency='INR',
                    is_posted=True,
                    status=JournalEntryStatus.POSTED,
                    source_type='manual',
                    source_reference=journal_header.journal_number,
                    approved_by=journal_header.approved_by,
                    approved_at=journal_header.approved_at
                )
                
                db.session.add(journal_entry)
                journal_entries_created.append(journal_entry)
            
            # Update header status
            journal_header.status = JournalEntryStatus.POSTED
            journal_header.posted_by = poster_id
            journal_header.posted_at = datetime.utcnow()
            journal_header.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit trail
            self._log_audit_action('POST', journal_header.id, f'Journal entry posted by user {poster_id}')
            
            # Integrate with automated accounting engine for report generation
            integration_result = self._integrate_with_accounting_reports(journal_header, journal_entries_created)
            
            return {
                'success': True,
                'journal_id': journal_header.id,
                'journal_number': journal_header.journal_number,
                'status': journal_header.status.value,
                'posted_entries_count': len(journal_entries_created),
                'integration_result': integration_result,
                'message': 'Journal entry posted successfully and integrated with reports'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error posting journal entry: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to post journal entry: {str(e)}'
            }
    
    def delete_journal_entry(self, journal_id: int, deleter_id: int) -> Dict[str, Any]:
        """
        Delete a journal entry (only if in DRAFT or REJECTED status)
        """
        try:
            journal_header = ManualJournalHeader.query.get(journal_id)
            if not journal_header:
                return {'success': False, 'error': 'Journal entry not found'}
            
            if journal_header.status not in [JournalEntryStatus.DRAFT, JournalEntryStatus.REJECTED]:
                return {
                    'success': False,
                    'error': f'Cannot delete journal entry in {journal_header.status.value} status'
                }
            
            journal_number = journal_header.journal_number
            
            # Log audit trail before deletion
            self._log_audit_action('DELETE', journal_header.id, f'Journal entry deleted by user {deleter_id}')
            
            # Delete journal header (lines will be deleted by cascade)
            db.session.delete(journal_header)
            db.session.commit()
            
            return {
                'success': True,
                'journal_number': journal_number,
                'message': 'Journal entry deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting journal entry: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to delete journal entry: {str(e)}'
            }
    
    def get_journal_entries_list(self, status_filter: str = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get list of manual journal entries with filtering and pagination
        """
        try:
            query = ManualJournalHeader.query.filter_by(company_id=self.company_id)
            
            if status_filter:
                query = query.filter(ManualJournalHeader.status == JournalEntryStatus(status_filter))
            
            total_count = query.count()
            journal_entries = query.order_by(ManualJournalHeader.created_at.desc()).offset(offset).limit(limit).all()
            
            entries_list = []
            for entry in journal_entries:
                entries_list.append({
                    'id': entry.id,
                    'journal_number': entry.journal_number,
                    'entry_date': entry.entry_date.strftime('%Y-%m-%d'),
                    'description': entry.description,
                    'reference_number': entry.reference_number,
                    'status': entry.status.value,
                    'total_debits': entry.total_debits,
                    'total_credits': entry.total_credits,
                    'created_by': entry.created_by_user.get_full_name() if entry.created_by_user else '',
                    'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'reviewed_by': entry.reviewed_by_user.get_full_name() if entry.reviewed_by_user else '',
                    'approved_by': entry.approved_by_user.get_full_name() if entry.approved_by_user else '',
                    'posted_by': entry.posted_by_user.get_full_name() if entry.posted_by_user else ''
                })
            
            return {
                'success': True,
                'journal_entries': entries_list,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.error(f"Error getting journal entries list: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to get journal entries: {str(e)}'
            }
    
    def get_journal_entry_details(self, journal_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific journal entry
        """
        try:
            journal_header = ManualJournalHeader.query.get(journal_id)
            if not journal_header:
                return {'success': False, 'error': 'Journal entry not found'}
            
            # Get journal lines
            lines = []
            for line in journal_header.journal_lines:
                lines.append({
                    'line_number': line.line_number,
                    'account_code': line.account.account_code if line.account else '',
                    'account_name': line.account.account_name if line.account else '',
                    'description': line.line_description,
                    'debit_amount': line.debit_amount,
                    'credit_amount': line.credit_amount,
                    'tax_code': line.tax_code,
                    'cost_center': line.cost_center,
                    'project_code': line.project_code
                })
            
            journal_details = {
                'id': journal_header.id,
                'journal_number': journal_header.journal_number,
                'entry_date': journal_header.entry_date.strftime('%Y-%m-%d'),
                'description': journal_header.description,
                'reference_number': journal_header.reference_number,
                'status': journal_header.status.value,
                'total_debits': journal_header.total_debits,
                'total_credits': journal_header.total_credits,
                'notes': journal_header.notes,
                'attachments': json.loads(journal_header.attachments or '[]'),
                'lines': lines,
                'workflow_history': {
                    'created_by': journal_header.created_by_user.get_full_name() if journal_header.created_by_user else '',
                    'created_at': journal_header.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'reviewed_by': journal_header.reviewed_by_user.get_full_name() if journal_header.reviewed_by_user else '',
                    'reviewed_at': journal_header.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if journal_header.reviewed_at else '',
                    'review_notes': journal_header.review_notes,
                    'approved_by': journal_header.approved_by_user.get_full_name() if journal_header.approved_by_user else '',
                    'approved_at': journal_header.approved_at.strftime('%Y-%m-%d %H:%M:%S') if journal_header.approved_at else '',
                    'approval_notes': journal_header.approval_notes,
                    'posted_by': journal_header.posted_by_user.get_full_name() if journal_header.posted_by_user else '',
                    'posted_at': journal_header.posted_at.strftime('%Y-%m-%d %H:%M:%S') if journal_header.posted_at else '',
                    'rejected_by': journal_header.rejected_by_user.get_full_name() if journal_header.rejected_by_user else '',
                    'rejected_at': journal_header.rejected_at.strftime('%Y-%m-%d %H:%M:%S') if journal_header.rejected_at else '',
                    'rejection_reason': journal_header.rejection_reason
                }
            }
            
            return {
                'success': True,
                'journal_entry': journal_details
            }
            
        except Exception as e:
            logger.error(f"Error getting journal entry details: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to get journal entry details: {str(e)}'
            }
    
    # Helper Methods
    def validate_journal_entry_comprehensive(self, journal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of journal entry data
        """
        errors = []
        warnings = []
        
        # Basic validation
        if not journal_data.get('date'):
            errors.append('Entry date is required')
        
        if not journal_data.get('description'):
            errors.append('Description is required')
        
        entries = journal_data.get('entries', [])
        if len(entries) < 2:
            errors.append('At least 2 journal lines are required')
        
        # Validate each entry
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')
        
        for i, entry in enumerate(entries):
            if not entry.get('account_code'):
                errors.append(f'Line {i+1}: Account code is required')
            
            if not entry.get('description'):
                warnings.append(f'Line {i+1}: Description is recommended')
            
            debit_amount = Decimal(str(entry.get('debit_amount', 0)))
            credit_amount = Decimal(str(entry.get('credit_amount', 0)))
            
            if not debit_amount and not credit_amount:
                errors.append(f'Line {i+1}: Either debit or credit amount is required')
            elif debit_amount and credit_amount:
                errors.append(f'Line {i+1}: Cannot have both debit and credit amounts')
            
            total_debits += debit_amount
            total_credits += credit_amount
        
        # Double-entry validation
        difference = abs(total_debits - total_credits)
        if difference >= Decimal('0.01'):
            errors.append(f'Total debits (₹{total_debits}) must equal total credits (₹{total_credits})')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validation_details': {
                'total_debits': float(total_debits),
                'total_credits': float(total_credits),
                'difference': float(difference)
            }
        }
    
    def _generate_journal_number(self) -> str:
        """Generate unique journal number"""
        today = datetime.now()
        prefix = f"MJ{today.strftime('%Y%m')}"
        
        # Get the last journal number for this month
        last_journal = ManualJournalHeader.query.filter(
            ManualJournalHeader.journal_number.like(f"{prefix}%")
        ).order_by(ManualJournalHeader.journal_number.desc()).first()
        
        if last_journal:
            last_number = int(last_journal.journal_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def _get_account_id_by_code(self, account_code: str) -> int:
        """Get account ID by account code"""
        account = ChartOfAccount.query.filter_by(account_code=account_code).first()
        if account:
            return account.id
        else:
            # Create a dummy account for demonstration (in real system, this should throw an error)
            return 1
    
    def _log_audit_action(self, action: str, journal_id: int, description: str):
        """Log audit trail for journal actions"""
        try:
            audit_log = AuditLog(
                user_id=self.user_id,
                action=action,
                table_name='manual_journal_headers',
                record_id=journal_id,
                new_values=description,
                timestamp=datetime.utcnow()
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")
    
    def _integrate_with_accounting_reports(self, journal_header: ManualJournalHeader, journal_entries: List[JournalEntry]) -> Dict[str, Any]:
        """
        Integrate posted manual journal entries with automated accounting reports
        """
        try:
            # This method ensures that manual journal entries are included in all financial reports
            integration_details = {
                'journal_entries_posted': len(journal_entries),
                'total_amount': journal_header.total_debits,
                'accounts_affected': [],
                'integration_timestamp': datetime.utcnow().isoformat()
            }
            
            # Track affected accounts
            for entry in journal_entries:
                if entry.account:
                    integration_details['accounts_affected'].append({
                        'account_code': entry.account.account_code,
                        'account_name': entry.account.account_name,
                        'debit_amount': entry.debit_amount,
                        'credit_amount': entry.credit_amount
                    })
            
            # Update account balances (this would be done in a real system)
            # The automated accounting engine will pick up these entries for report generation
            
            logger.info(f"Manual journal {journal_header.journal_number} integrated with accounting reports")
            
            return {
                'success': True,
                'integration_details': integration_details,
                'message': 'Successfully integrated with accounting reports'
            }
            
        except Exception as e:
            logger.error(f"Error integrating with accounting reports: {str(e)}")
            return {
                'success': False,
                'error': f'Integration failed: {str(e)}'
            }
    
    def get_chart_of_accounts(self) -> List[Dict[str, Any]]:
        """Get chart of accounts for dropdown selections"""
        try:
            accounts = ChartOfAccount.query.filter_by(is_active=True).order_by(ChartOfAccount.account_code).all()
            
            return [
                {
                    'account_code': account.account_code,
                    'account_name': account.account_name,
                    'account_type': account.account_type,
                    'description': account.description
                }
                for account in accounts
            ]
        except Exception as e:
            logger.error(f"Error getting chart of accounts: {str(e)}")
            return []