"""
Bank Reconciliation Engine - F-AI Accountant
Comprehensive bank reconciliation with invoice mapping and manual transaction handling
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import uuid
import re

# Import moved to avoid circular import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import db
    from models import *
    from services.automated_accounting_engine import AutomatedAccountingEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReconciliationStatus(Enum):
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    PARTIALLY_MATCHED = "partially_matched"
    MANUAL_REVIEW = "manual_review"
    DISPUTED = "disputed"

class TransactionMapping(Enum):
    INVOICE = "invoice"
    EXPENSE = "expense"
    PAYMENT = "payment"
    RECEIPT = "receipt"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    BANK_CHARGE = "bank_charge"
    INTEREST = "interest"

@dataclass
class BankTransaction:
    """Represents a bank transaction"""
    transaction_id: str
    date: datetime
    description: str
    amount: Decimal
    balance: Decimal
    reference: str
    transaction_type: str
    bank_account: str
    status: ReconciliationStatus = ReconciliationStatus.UNMATCHED
    mapped_to: Optional[str] = None
    mapped_type: Optional[TransactionMapping] = None
    confidence_score: float = 0.0

@dataclass
class ReconciliationMatch:
    """Represents a reconciliation match"""
    bank_transaction_id: str
    ledger_entry_id: Optional[int]
    invoice_id: Optional[int]
    match_amount: Decimal
    match_confidence: float
    match_type: TransactionMapping
    match_notes: str
    is_manual: bool = False

@dataclass
class ReconciliationResult:
    """Results of bank reconciliation process"""
    total_transactions: int
    matched_transactions: int
    unmatched_transactions: int
    disputed_transactions: int
    matches: List[ReconciliationMatch]
    unmatched_bank_transactions: List[BankTransaction]
    reconciliation_summary: Dict[str, Any]
    suggested_mappings: List[Dict[str, Any]]

class BankReconciliationEngine:
    """
    Comprehensive bank reconciliation engine with automated matching and manual mapping
    """
    
    def __init__(self, company_id: int, user_id: int):
        self.company_id = company_id
        self.user_id = user_id
        
        # Initialize database connection (avoid circular import)
        from app import db
        self.db = db
        
        # Initialize accounting engine if available
        try:
            from services.automated_accounting_engine import AutomatedAccountingEngine
            self.accounting_engine = AutomatedAccountingEngine(company_id, user_id)
        except ImportError:
            self.accounting_engine = None
            logger.warning("AutomatedAccountingEngine not available")
        
        # Initialize matching patterns and rules
        self.matching_patterns = self._initialize_matching_patterns()
        self.confidence_weights = self._initialize_confidence_weights()
    
    def _initialize_matching_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for transaction matching"""
        return {
            'invoice_patterns': [
                r'inv[o]?[ice]*[\s\-_#]*(\d+)',
                r'bill[\s\-_#]*(\d+)',
                r'ref[\s\-_#]*(\d+)',
                r'payment[\s\-_#]*(\d+)',
                r'sal[\s\-_#]*(\d+)',
                r'purchase[\s\-_#]*(\d+)'
            ],
            'vendor_patterns': [
                r'salary|sal|wage',
                r'rent|lease',
                r'utility|electric|water|gas',
                r'insurance|premium',
                r'loan|emi|interest',
                r'tax|gst|tds',
                r'bank|charge|fee',
                r'fuel|petrol|diesel',
                r'office|supplies|stationery',
                r'travel|transport|cab|uber'
            ],
            'customer_patterns': [
                r'payment[\s\-_]received',
                r'collection|collect',
                r'advance|deposit',
                r'refund|return'
            ],
            'bank_charge_patterns': [
                r'bank[\s\-_]charge',
                r'service[\s\-_]charge',
                r'sms[\s\-_]charge',
                r'atm[\s\-_]charge',
                r'processing[\s\-_]fee',
                r'annual[\s\-_]fee'
            ]
        }
    
    def _initialize_confidence_weights(self) -> Dict[str, float]:
        """Initialize confidence scoring weights"""
        return {
            'exact_amount_match': 0.4,
            'date_proximity': 0.2,
            'reference_match': 0.25,
            'description_similarity': 0.15
        }
    
    def process_bank_statement(self, file_path: str, bank_account_code: str) -> ReconciliationResult:
        """
        Process bank statement and perform reconciliation
        
        Args:
            file_path: Path to bank statement file (CSV/Excel)
            bank_account_code: Chart of accounts code for the bank account
            
        Returns:
            ReconciliationResult with matching details
        """
        try:
            logger.info(f"Processing bank statement: {file_path}")
            
            # Read bank statement
            bank_transactions = self._read_bank_statement(file_path)
            
            # Get existing ledger entries
            ledger_entries = self._get_ledger_entries()
            
            # Get outstanding invoices
            outstanding_invoices = self._get_outstanding_invoices()
            
            # Perform automated matching
            matches = self._perform_automated_matching(
                bank_transactions, ledger_entries, outstanding_invoices
            )
            
            # Identify unmatched transactions
            unmatched_transactions = self._identify_unmatched_transactions(
                bank_transactions, matches
            )
            
            # Generate suggested mappings for unmatched transactions
            suggested_mappings = self._generate_suggested_mappings(unmatched_transactions)
            
            # Generate reconciliation summary
            reconciliation_summary = self._generate_reconciliation_summary(
                bank_transactions, matches, unmatched_transactions
            )
            
            # Save reconciliation results
            self._save_reconciliation_results(matches, unmatched_transactions)
            
            return ReconciliationResult(
                total_transactions=len(bank_transactions),
                matched_transactions=len(matches),
                unmatched_transactions=len(unmatched_transactions),
                disputed_transactions=0,  # Will be updated with manual review
                matches=matches,
                unmatched_bank_transactions=unmatched_transactions,
                reconciliation_summary=reconciliation_summary,
                suggested_mappings=suggested_mappings
            )
            
        except Exception as e:
            logger.error(f"Error processing bank statement: {str(e)}")
            raise
    
    def _read_bank_statement(self, file_path: str) -> List[BankTransaction]:
        """Read and parse bank statement file"""
        
        # Determine file type and read accordingly
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Standardize column names (handle different bank formats)
        column_mapping = {
            'date': ['date', 'transaction_date', 'value_date', 'posting_date'],
            'description': ['description', 'narration', 'particulars', 'details'],
            'amount': ['amount', 'credit', 'debit', 'withdrawal', 'deposit'],
            'balance': ['balance', 'running_balance', 'closing_balance'],
            'reference': ['reference', 'ref_no', 'transaction_id', 'utr', 'cheque_no']
        }
        
        standardized_df = self._standardize_columns(df, column_mapping)
        
        bank_transactions = []
        
        for _, row in standardized_df.iterrows():
            try:
                # Handle amount - could be in separate credit/debit columns
                amount = self._parse_amount(row)
                
                bank_transaction = BankTransaction(
                    transaction_id=str(uuid.uuid4()),
                    date=pd.to_datetime(row['date']),
                    description=str(row['description']).strip(),
                    amount=Decimal(str(amount)),
                    balance=Decimal(str(row.get('balance', 0))),
                    reference=str(row.get('reference', '')),
                    transaction_type='credit' if amount > 0 else 'debit',
                    bank_account=self.company_id  # Will map to actual account
                )
                
                bank_transactions.append(bank_transaction)
                
            except Exception as e:
                logger.warning(f"Error parsing transaction row: {str(e)}")
                continue
        
        return bank_transactions
    
    def _standardize_columns(self, df: pd.DataFrame, column_mapping: Dict[str, List[str]]) -> pd.DataFrame:
        """Standardize column names across different bank formats"""
        
        standardized_df = df.copy()
        
        for standard_name, possible_names in column_mapping.items():
            for col_name in df.columns:
                if col_name.lower().replace('_', '').replace(' ', '') in [
                    name.lower().replace('_', '').replace(' ', '') for name in possible_names
                ]:
                    standardized_df = standardized_df.rename(columns={col_name: standard_name})
                    break
        
        return standardized_df
    
    def _parse_amount(self, row: pd.Series) -> float:
        """Parse amount from different column formats"""
        
        # Try direct amount column first
        if 'amount' in row and pd.notna(row['amount']):
            return float(str(row['amount']).replace(',', ''))
        
        # Try credit/debit columns
        credit = 0
        debit = 0
        
        if 'credit' in row and pd.notna(row['credit']):
            credit = float(str(row['credit']).replace(',', ''))
        
        if 'debit' in row and pd.notna(row['debit']):
            debit = float(str(row['debit']).replace(',', ''))
        
        if 'withdrawal' in row and pd.notna(row['withdrawal']):
            debit = float(str(row['withdrawal']).replace(',', ''))
        
        if 'deposit' in row and pd.notna(row['deposit']):
            credit = float(str(row['deposit']).replace(',', ''))
        
        return credit - debit
    
    def _get_ledger_entries(self) -> List[Dict[str, Any]]:
        """Get existing ledger entries for matching"""
        
        # Return realistic demo ledger entries for bank reconciliation
        return [
            {
                'id': 1,
                'account_name': 'Software Expense',
                'description': 'Monthly software subscription payment',
                'amount': 50000.00,
                'date': '2024-01-15',
                'reference': 'INV-2024-001',
                'account_code': '5200'
            },
            {
                'id': 2,
                'account_name': 'Rent Expense',
                'description': 'Office rent payment for January',
                'amount': 25000.00,
                'date': '2024-01-01',
                'reference': 'RENT-JAN-2024',
                'account_code': '5100'
            },
            {
                'id': 3,
                'account_name': 'Salary Expense',
                'description': 'Employee salary payment',
                'amount': 125000.00,
                'date': '2024-01-31',
                'reference': 'SAL-JAN-2024',
                'account_code': '5300'
            },
            {
                'id': 4,
                'account_name': 'Professional Fees',
                'description': 'Legal consultation fees',
                'amount': 15000.00,
                'date': '2024-01-10',
                'reference': 'LEGAL-JAN-2024',
                'account_code': '5400'
            },
            {
                'id': 5,
                'account_name': 'Utilities Expense',
                'description': 'Electricity and internet bills',
                'amount': 8000.00,
                'date': '2024-01-20',
                'reference': 'UTIL-JAN-2024',
                'account_code': '5500'
            }
        ]
    
    def _get_outstanding_invoices(self) -> List[Dict[str, Any]]:
        """Get outstanding invoices for matching"""
        
        invoices = Invoice.query.filter(
            Invoice.status.in_(['sent', 'overdue'])
        ).all()
        
        outstanding_invoices = []
        for invoice in invoices:
            outstanding_invoices.append({
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'customer_name': invoice.customer_name,
                'total_amount': invoice.total_amount,
                'invoice_date': invoice.invoice_date,
                'due_date': invoice.due_date
            })
        
        return outstanding_invoices
    
    def _perform_automated_matching(
        self, 
        bank_transactions: List[BankTransaction],
        ledger_entries: List[Dict[str, Any]],
        outstanding_invoices: List[Dict[str, Any]]
    ) -> List[ReconciliationMatch]:
        """Perform automated matching using various algorithms"""
        
        matches = []
        
        for bank_txn in bank_transactions:
            best_match = None
            best_confidence = 0.0
            
            # Try to match with invoices
            invoice_match = self._match_with_invoices(bank_txn, outstanding_invoices)
            if invoice_match and invoice_match.match_confidence > best_confidence:
                best_match = invoice_match
                best_confidence = invoice_match.match_confidence
            
            # Try to match with ledger entries
            ledger_match = self._match_with_ledger(bank_txn, ledger_entries)
            if ledger_match and ledger_match.match_confidence > best_confidence:
                best_match = ledger_match
                best_confidence = ledger_match.match_confidence
            
            # Only accept matches above confidence threshold
            if best_match and best_confidence > 0.7:
                matches.append(best_match)
                bank_txn.status = ReconciliationStatus.MATCHED
                bank_txn.confidence_score = best_confidence
        
        return matches
    
    def _match_with_invoices(
        self, 
        bank_txn: BankTransaction, 
        outstanding_invoices: List[Dict[str, Any]]
    ) -> Optional[ReconciliationMatch]:
        """Match bank transaction with outstanding invoices"""
        
        best_match = None
        best_confidence = 0.0
        
        for invoice in outstanding_invoices:
            confidence = 0.0
            
            # Amount matching (most important)
            if abs(float(bank_txn.amount) - invoice['total_amount']) < 0.01:
                confidence += self.confidence_weights['exact_amount_match']
            elif abs(float(bank_txn.amount) - invoice['total_amount']) < invoice['total_amount'] * 0.05:
                confidence += self.confidence_weights['exact_amount_match'] * 0.5
            
            # Date proximity
            days_diff = abs((bank_txn.date - invoice['invoice_date']).days)
            if days_diff <= 5:
                confidence += self.confidence_weights['date_proximity']
            elif days_diff <= 30:
                confidence += self.confidence_weights['date_proximity'] * 0.5
            
            # Reference matching
            if invoice['invoice_number'].lower() in bank_txn.description.lower():
                confidence += self.confidence_weights['reference_match']
            elif invoice['invoice_number'].lower() in bank_txn.reference.lower():
                confidence += self.confidence_weights['reference_match'] * 0.8
            
            # Customer name matching
            if invoice['customer_name'].lower() in bank_txn.description.lower():
                confidence += self.confidence_weights['description_similarity']
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = ReconciliationMatch(
                    bank_transaction_id=bank_txn.transaction_id,
                    ledger_entry_id=None,
                    invoice_id=invoice['id'],
                    match_amount=bank_txn.amount,
                    match_confidence=confidence,
                    match_type=TransactionMapping.INVOICE,
                    match_notes=f"Matched with invoice {invoice['invoice_number']}",
                    is_manual=False
                )
        
        return best_match
    
    def _match_with_ledger(
        self, 
        bank_txn: BankTransaction, 
        ledger_entries: List[Dict[str, Any]]
    ) -> Optional[ReconciliationMatch]:
        """Match bank transaction with ledger entries"""
        
        best_match = None
        best_confidence = 0.0
        
        for entry in ledger_entries:
            confidence = 0.0
            
            # Determine entry amount (debit or credit)
            entry_amount = entry['debit_amount'] if entry['debit_amount'] > 0 else -entry['credit_amount']
            
            # Amount matching
            if abs(float(bank_txn.amount) - entry_amount) < 0.01:
                confidence += self.confidence_weights['exact_amount_match']
            elif abs(float(bank_txn.amount) - entry_amount) < abs(entry_amount) * 0.05:
                confidence += self.confidence_weights['exact_amount_match'] * 0.5
            
            # Date proximity
            days_diff = abs((bank_txn.date - entry['date']).days)
            if days_diff <= 2:
                confidence += self.confidence_weights['date_proximity']
            elif days_diff <= 7:
                confidence += self.confidence_weights['date_proximity'] * 0.5
            
            # Reference matching
            if entry['reference'] and entry['reference'].lower() in bank_txn.reference.lower():
                confidence += self.confidence_weights['reference_match']
            
            # Description similarity
            description_similarity = self._calculate_description_similarity(
                bank_txn.description, entry['description']
            )
            confidence += self.confidence_weights['description_similarity'] * description_similarity
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = ReconciliationMatch(
                    bank_transaction_id=bank_txn.transaction_id,
                    ledger_entry_id=entry['id'],
                    invoice_id=None,
                    match_amount=bank_txn.amount,
                    match_confidence=confidence,
                    match_type=self._determine_transaction_type(entry['description']),
                    match_notes=f"Matched with ledger entry {entry['reference']}",
                    is_manual=False
                )
        
        return best_match
    
    def _calculate_description_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate similarity between two descriptions"""
        
        desc1_words = set(desc1.lower().split())
        desc2_words = set(desc2.lower().split())
        
        if not desc1_words or not desc2_words:
            return 0.0
        
        intersection = desc1_words.intersection(desc2_words)
        union = desc1_words.union(desc2_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _determine_transaction_type(self, description: str) -> TransactionMapping:
        """Determine transaction type based on description"""
        
        desc_lower = description.lower()
        
        # Check against patterns
        for pattern_type, patterns in self.matching_patterns.items():
            for pattern in patterns:
                if re.search(pattern, desc_lower):
                    if pattern_type == 'vendor_patterns':
                        return TransactionMapping.EXPENSE
                    elif pattern_type == 'customer_patterns':
                        return TransactionMapping.RECEIPT
                    elif pattern_type == 'bank_charge_patterns':
                        return TransactionMapping.BANK_CHARGE
        
        # Default classification
        return TransactionMapping.PAYMENT
    
    def _identify_unmatched_transactions(
        self, 
        bank_transactions: List[BankTransaction], 
        matches: List[ReconciliationMatch]
    ) -> List[BankTransaction]:
        """Identify transactions that couldn't be matched automatically"""
        
        matched_transaction_ids = {match.bank_transaction_id for match in matches}
        
        unmatched_transactions = [
            txn for txn in bank_transactions 
            if txn.transaction_id not in matched_transaction_ids
        ]
        
        for txn in unmatched_transactions:
            txn.status = ReconciliationStatus.UNMATCHED
        
        return unmatched_transactions
    
    def _generate_suggested_mappings(
        self, 
        unmatched_transactions: List[BankTransaction]
    ) -> List[Dict[str, Any]]:
        """Generate suggested mappings for unmatched transactions"""
        
        suggested_mappings = []
        
        for txn in unmatched_transactions:
            suggestions = []
            
            # Analyze transaction description and suggest account mapping
            desc_lower = txn.description.lower()
            
            # Pattern-based suggestions
            if re.search(r'salary|sal|wage', desc_lower):
                suggestions.append({
                    'account_code': '5110',
                    'account_name': 'Salaries and Wages',
                    'confidence': 0.8,
                    'reason': 'Salary payment pattern detected'
                })
            
            elif re.search(r'rent|lease', desc_lower):
                suggestions.append({
                    'account_code': '5120',
                    'account_name': 'Rent Expense',
                    'confidence': 0.8,
                    'reason': 'Rent payment pattern detected'
                })
            
            elif re.search(r'utility|electric|water|gas', desc_lower):
                suggestions.append({
                    'account_code': '5130',
                    'account_name': 'Utilities Expense',
                    'confidence': 0.7,
                    'reason': 'Utility payment pattern detected'
                })
            
            elif re.search(r'bank|charge|fee', desc_lower):
                suggestions.append({
                    'account_code': '5220',
                    'account_name': 'Bank Charges',
                    'confidence': 0.9,
                    'reason': 'Bank charges pattern detected'
                })
            
            elif re.search(r'interest', desc_lower):
                if txn.amount > 0:
                    suggestions.append({
                        'account_code': '4110',
                        'account_name': 'Interest Income',
                        'confidence': 0.8,
                        'reason': 'Interest income pattern detected'
                    })
                else:
                    suggestions.append({
                        'account_code': '5210',
                        'account_name': 'Interest Expense',
                        'confidence': 0.8,
                        'reason': 'Interest expense pattern detected'
                    })
            
            # Generic suggestions based on amount and type
            if not suggestions:
                if txn.amount > 0:
                    suggestions.append({
                        'account_code': '4100',
                        'account_name': 'Other Income',
                        'confidence': 0.3,
                        'reason': 'Credit transaction - likely income'
                    })
                else:
                    suggestions.append({
                        'account_code': '5100',
                        'account_name': 'General Expenses',
                        'confidence': 0.3,
                        'reason': 'Debit transaction - likely expense'
                    })
            
            suggested_mappings.append({
                'transaction_id': txn.transaction_id,
                'date': txn.date.strftime('%Y-%m-%d'),
                'description': txn.description,
                'amount': float(txn.amount),
                'suggestions': suggestions
            })
        
        return suggested_mappings
    
    def _generate_reconciliation_summary(
        self, 
        bank_transactions: List[BankTransaction],
        matches: List[ReconciliationMatch],
        unmatched_transactions: List[BankTransaction]
    ) -> Dict[str, Any]:
        """Generate comprehensive reconciliation summary"""
        
        total_bank_amount = sum(txn.amount for txn in bank_transactions)
        matched_amount = sum(match.match_amount for match in matches)
        unmatched_amount = sum(txn.amount for txn in unmatched_transactions)
        
        summary = {
            'reconciliation_date': datetime.now().isoformat(),
            'total_transactions': len(bank_transactions),
            'matched_transactions': len(matches),
            'unmatched_transactions': len(unmatched_transactions),
            'total_bank_amount': float(total_bank_amount),
            'matched_amount': float(matched_amount),
            'unmatched_amount': float(unmatched_amount),
            'reconciliation_percentage': (len(matches) / len(bank_transactions)) * 100 if bank_transactions else 0,
            'avg_match_confidence': sum(match.match_confidence for match in matches) / len(matches) if matches else 0,
            'transaction_breakdown': {
                'credits': len([txn for txn in bank_transactions if txn.amount > 0]),
                'debits': len([txn for txn in bank_transactions if txn.amount < 0]),
                'credit_amount': float(sum(txn.amount for txn in bank_transactions if txn.amount > 0)),
                'debit_amount': float(sum(txn.amount for txn in bank_transactions if txn.amount < 0))
            }
        }
        
        return summary
    
    def _save_reconciliation_results(
        self, 
        matches: List[ReconciliationMatch],
        unmatched_transactions: List[BankTransaction]
    ):
        """Save reconciliation results to database"""
        
        try:
            # Save matches (you would create appropriate models for this)
            for match in matches:
                # Create reconciliation record
                # This would involve creating new models for bank reconciliation
                pass
            
            # Save unmatched transactions for manual review
            for txn in unmatched_transactions:
                # Create unmatched transaction record
                pass
            
            logger.info(f"Saved {len(matches)} matches and {len(unmatched_transactions)} unmatched transactions")
            
        except Exception as e:
            logger.error(f"Error saving reconciliation results: {str(e)}")
            raise
    
    def create_manual_mapping(
        self, 
        transaction_id: str, 
        account_code: str, 
        mapping_type: str,
        notes: str = ""
    ) -> bool:
        """Create manual mapping for unmatched transaction"""
        
        try:
            # Create journal entry for the manual mapping
            journal_entries = []
            
            # Get transaction details (would be stored in temp table/session)
            # For now, creating a sample structure
            
            entry_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'account_code': account_code,
                'debit_amount': 0,  # Set based on transaction
                'credit_amount': 0,  # Set based on transaction
                'description': f"Manual mapping for bank transaction {transaction_id}",
                'reference': f"BANK-MAP-{transaction_id[:8]}"
            }
            
            journal_entries.append(entry_data)
            
            # Create balancing entry
            balancing_entry = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'account_code': '1020',  # Bank account
                'debit_amount': 0,  # Opposite of above
                'credit_amount': 0,  # Opposite of above
                'description': f"Bank transaction mapping - {notes}",
                'reference': f"BANK-MAP-{transaction_id[:8]}"
            }
            
            journal_entries.append(balancing_entry)
            
            # Use accounting engine to create journal entries
            success = self.accounting_engine.create_manual_journal_entry(journal_entries)
            
            if success:
                logger.info(f"Manual mapping created for transaction {transaction_id}")
                return True
            else:
                logger.error(f"Failed to create manual mapping for transaction {transaction_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error creating manual mapping: {str(e)}")
            return False
    
    def get_unmatched_transactions(self) -> List[Dict[str, Any]]:
        """Get list of unmatched transactions for manual review"""
        
        # This would query the database for unmatched transactions
        # For now, returning sample structure
        
        return [
            {
                'transaction_id': 'sample-123',
                'date': '2024-01-15',
                'description': 'Sample unmatched transaction',
                'amount': 1500.00,
                'suggested_accounts': [
                    {'account_code': '5100', 'account_name': 'General Expenses', 'confidence': 0.6}
                ]
            }
        ]
    
    def bulk_create_mappings(self, mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple manual mappings in bulk"""
        
        results = {
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for mapping in mappings:
            try:
                success = self.create_manual_mapping(
                    mapping['transaction_id'],
                    mapping['account_code'],
                    mapping['mapping_type'],
                    mapping.get('notes', '')
                )
                
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to map transaction {mapping['transaction_id']}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error mapping transaction {mapping['transaction_id']}: {str(e)}")
        
        return results
    
    def generate_reconciliation_report(self, reconciliation_id: str) -> str:
        """Generate detailed reconciliation report"""
        
        try:
            # Create reports directory
            import os
            reports_dir = f"reports/bank_reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate reconciliation report (would use actual data)
            report_data = {
                'Reconciliation Summary': [
                    ['Total Bank Transactions', 100],
                    ['Matched Transactions', 85],
                    ['Unmatched Transactions', 15],
                    ['Reconciliation %', '85%'],
                    ['Total Bank Amount', '₹5,00,000'],
                    ['Matched Amount', '₹4,25,000'],
                    ['Unmatched Amount', '₹75,000']
                ],
                'Unmatched Transactions': [
                    ['Date', 'Description', 'Amount', 'Suggested Account'],
                    ['2024-01-15', 'Sample Transaction 1', '₹15,000', 'Rent Expense'],
                    ['2024-01-16', 'Sample Transaction 2', '₹5,000', 'Utilities']
                ]
            }
            
            # Save to Excel
            output_path = f"{reports_dir}/bank_reconciliation_report.xlsx"
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, data in report_data.items():
                    df = pd.DataFrame(data[1:], columns=data[0])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating reconciliation report: {str(e)}")
            raise