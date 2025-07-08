"""
Advanced Bank Reconciliation Engine
Professional-grade bank reconciliation with automatic invoice mapping and intelligent transaction matching
"""

import pandas as pd
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
from dataclasses import dataclass
from enum import Enum

class MatchConfidence(Enum):
    PERFECT = "PERFECT"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    UNMAPPED = "UNMAPPED"

@dataclass
class TransactionMatch:
    bank_transaction_id: str
    invoice_id: Optional[str]
    confidence_level: MatchConfidence
    confidence_score: float
    mapping_factors: Dict[str, float]
    manual_review_required: bool
    suggested_account: Optional[str]
    notes: str

@dataclass
class BankTransaction:
    transaction_id: str
    date: datetime
    description: str
    amount: float
    reference: str
    balance: float
    transaction_type: str  # credit/debit
    matched: bool = False
    matched_invoice_id: Optional[str] = None
    confidence_score: float = 0.0

@dataclass
class Invoice:
    invoice_id: str
    invoice_number: str
    party_name: str
    amount: float
    date: datetime
    description: str
    gst_number: Optional[str]
    transaction_type: str  # sales/purchase
    matched: bool = False
    matched_bank_transaction_id: Optional[str] = None

class AdvancedBankReconciliationEngine:
    """
    Advanced bank reconciliation engine with professional invoice mapping capabilities
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bank_transactions: List[BankTransaction] = []
        self.invoices: List[Invoice] = []
        self.matches: List[TransactionMatch] = []
        self.reconciliation_summary = {}
        
        # Professional mapping weights
        self.mapping_weights = {
            'amount_match': 0.35,
            'date_proximity': 0.25,
            'reference_match': 0.20,
            'party_name_match': 0.15,
            'description_similarity': 0.05
        }
        
        # Account mapping rules
        self.account_mapping_rules = {
            'sales_receipt': '1100',  # Bank Account (Asset)
            'purchase_payment': '1100',  # Bank Account (Asset)
            'expense_payment': '1100',  # Bank Account (Asset)
            'loan_receipt': '2200',  # Long-term Debt (Liability)
            'interest_payment': '5500',  # Interest Expense
            'salary_payment': '5300',  # Salary Expense
            'utility_payment': '5200',  # Utilities Expense
            'rent_payment': '5100',  # Rent Expense
            'tax_payment': '2300',  # Tax Payable
            'dividend_payment': '3200',  # Dividends
            'asset_purchase': '1500',  # Fixed Assets
            'miscellaneous': '5000'   # General Expenses
        }
    
    def load_bank_statement(self, bank_data: List[Dict]) -> bool:
        """Load bank statement data"""
        try:
            self.bank_transactions = []
            for idx, row in enumerate(bank_data):
                transaction = BankTransaction(
                    transaction_id=f"BT_{idx+1}",
                    date=datetime.strptime(str(row['date']), '%Y-%m-%d') if isinstance(row['date'], str) else row['date'],
                    description=str(row['description']),
                    amount=float(row['amount']),
                    reference=str(row.get('reference', '')),
                    balance=float(row.get('balance', 0)),
                    transaction_type='credit' if float(row['amount']) > 0 else 'debit'
                )
                self.bank_transactions.append(transaction)
            
            self.logger.info(f"Loaded {len(self.bank_transactions)} bank transactions")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading bank statement: {str(e)}")
            return False
    
    def load_invoice_data(self, invoice_data: List[Dict]) -> bool:
        """Load invoice data for mapping"""
        try:
            self.invoices = []
            for idx, row in enumerate(invoice_data):
                invoice = Invoice(
                    invoice_id=f"INV_{idx+1}",
                    invoice_number=str(row['invoice_number']),
                    party_name=str(row['party_name']),
                    amount=float(row['amount']),
                    date=datetime.strptime(str(row['date']), '%Y-%m-%d') if isinstance(row['date'], str) else row['date'],
                    description=str(row['description']),
                    gst_number=str(row.get('gst_number', '')),
                    transaction_type=str(row.get('transaction_type', 'sales'))
                )
                self.invoices.append(invoice)
            
            self.logger.info(f"Loaded {len(self.invoices)} invoices")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading invoice data: {str(e)}")
            return False
    
    def calculate_amount_match_score(self, bank_amount: float, invoice_amount: float) -> float:
        """Calculate amount matching score with GST consideration"""
        # Direct amount match
        if abs(bank_amount - invoice_amount) < 0.01:
            return 1.0
        
        # Check for GST inclusive/exclusive matching
        gst_rates = [0.18, 0.12, 0.05, 0.28]  # Common GST rates
        
        for rate in gst_rates:
            # Bank amount might be GST inclusive
            gst_exclusive = bank_amount / (1 + rate)
            if abs(gst_exclusive - invoice_amount) < 0.01:
                return 0.95
            
            # Invoice amount might be GST exclusive
            gst_inclusive = invoice_amount * (1 + rate)
            if abs(bank_amount - gst_inclusive) < 0.01:
                return 0.95
        
        # Percentage difference calculation
        max_amount = max(abs(bank_amount), abs(invoice_amount))
        if max_amount > 0:
            difference_percent = abs(bank_amount - invoice_amount) / max_amount
            return max(0, 1 - difference_percent)
        
        return 0.0
    
    def calculate_date_proximity_score(self, bank_date: datetime, invoice_date: datetime) -> float:
        """Calculate date proximity score"""
        days_diff = abs((bank_date - invoice_date).days)
        
        if days_diff == 0:
            return 1.0
        elif days_diff <= 3:
            return 0.9
        elif days_diff <= 7:
            return 0.7
        elif days_diff <= 15:
            return 0.5
        elif days_diff <= 30:
            return 0.3
        else:
            return 0.1
    
    def calculate_reference_match_score(self, bank_ref: str, invoice_number: str) -> float:
        """Calculate reference matching score"""
        if not bank_ref or not invoice_number:
            return 0.0
        
        # Clean references
        bank_ref_clean = re.sub(r'[^a-zA-Z0-9]', '', bank_ref.upper())
        invoice_clean = re.sub(r'[^a-zA-Z0-9]', '', invoice_number.upper())
        
        # Exact match
        if bank_ref_clean == invoice_clean:
            return 1.0
        
        # Check if invoice number is contained in bank reference
        if invoice_clean in bank_ref_clean:
            return 0.8
        
        # Check for partial matches
        if len(invoice_clean) >= 4:
            # Check if last 4 characters match
            if invoice_clean[-4:] in bank_ref_clean:
                return 0.6
        
        return 0.0
    
    def calculate_party_name_match_score(self, bank_desc: str, party_name: str) -> float:
        """Calculate party name matching score"""
        if not bank_desc or not party_name:
            return 0.0
        
        # Clean names
        bank_desc_clean = re.sub(r'[^a-zA-Z0-9\s]', '', bank_desc.upper())
        party_clean = re.sub(r'[^a-zA-Z0-9\s]', '', party_name.upper())
        
        # Split into words
        bank_words = set(bank_desc_clean.split())
        party_words = set(party_clean.split())
        
        # Remove common words
        common_words = {'LTD', 'LIMITED', 'PVT', 'PRIVATE', 'CO', 'COMPANY', 'INC', 'INCORPORATED'}
        bank_words -= common_words
        party_words -= common_words
        
        if not party_words:
            return 0.0
        
        # Calculate word matching percentage
        matching_words = bank_words & party_words
        return len(matching_words) / len(party_words)
    
    def calculate_description_similarity(self, bank_desc: str, invoice_desc: str) -> float:
        """Calculate description similarity score"""
        if not bank_desc or not invoice_desc:
            return 0.0
        
        # Common business transaction keywords
        keywords = ['SOFTWARE', 'DEVELOPMENT', 'SERVICES', 'PAYMENT', 'INVOICE', 
                   'CONSULTING', 'DESIGN', 'MARKETING', 'OFFICE', 'SUPPLIES']
        
        bank_desc_upper = bank_desc.upper()
        invoice_desc_upper = invoice_desc.upper()
        
        matching_keywords = 0
        for keyword in keywords:
            if keyword in bank_desc_upper and keyword in invoice_desc_upper:
                matching_keywords += 1
        
        return matching_keywords / len(keywords) if keywords else 0.0
    
    def find_best_match(self, bank_transaction: BankTransaction) -> Optional[TransactionMatch]:
        """Find the best matching invoice for a bank transaction"""
        best_match = None
        best_score = 0.0
        
        for invoice in self.invoices:
            if invoice.matched:
                continue
            
            # Calculate individual factor scores
            amount_score = self.calculate_amount_match_score(
                abs(bank_transaction.amount), invoice.amount
            )
            date_score = self.calculate_date_proximity_score(
                bank_transaction.date, invoice.date
            )
            reference_score = self.calculate_reference_match_score(
                bank_transaction.reference, invoice.invoice_number
            )
            party_score = self.calculate_party_name_match_score(
                bank_transaction.description, invoice.party_name
            )
            description_score = self.calculate_description_similarity(
                bank_transaction.description, invoice.description
            )
            
            # Calculate weighted total score
            total_score = (
                amount_score * self.mapping_weights['amount_match'] +
                date_score * self.mapping_weights['date_proximity'] +
                reference_score * self.mapping_weights['reference_match'] +
                party_score * self.mapping_weights['party_name_match'] +
                description_score * self.mapping_weights['description_similarity']
            )
            
            if total_score > best_score:
                best_score = total_score
                
                # Determine confidence level
                if total_score >= 0.95:
                    confidence_level = MatchConfidence.PERFECT
                elif total_score >= 0.80:
                    confidence_level = MatchConfidence.HIGH
                elif total_score >= 0.60:
                    confidence_level = MatchConfidence.MODERATE
                elif total_score >= 0.40:
                    confidence_level = MatchConfidence.LOW
                else:
                    confidence_level = MatchConfidence.UNMAPPED
                
                best_match = TransactionMatch(
                    bank_transaction_id=bank_transaction.transaction_id,
                    invoice_id=invoice.invoice_id,
                    confidence_level=confidence_level,
                    confidence_score=total_score,
                    mapping_factors={
                        'amount_match': amount_score,
                        'date_proximity': date_score,
                        'reference_match': reference_score,
                        'party_name_match': party_score,
                        'description_similarity': description_score
                    },
                    manual_review_required=total_score < 0.80,
                    suggested_account=self.get_suggested_account(bank_transaction, invoice),
                    notes=f"Auto-mapped with {total_score:.2%} confidence"
                )
        
        return best_match
    
    def get_suggested_account(self, bank_transaction: BankTransaction, invoice: Invoice) -> str:
        """Get suggested account code based on transaction type"""
        if bank_transaction.transaction_type == 'credit':
            if invoice.transaction_type == 'sales':
                return self.account_mapping_rules['sales_receipt']
        else:  # debit
            if invoice.transaction_type == 'purchase':
                return self.account_mapping_rules['purchase_payment']
        
        return self.account_mapping_rules['miscellaneous']
    
    def perform_automatic_mapping(self) -> Dict[str, Any]:
        """Perform automatic invoice mapping for all bank transactions"""
        self.matches = []
        mapping_results = {
            'perfect_matches': [],
            'high_confidence_matches': [],
            'moderate_matches': [],
            'low_confidence_matches': [],
            'unmapped_transactions': []
        }
        
        for bank_transaction in self.bank_transactions:
            if bank_transaction.matched:
                continue
            
            best_match = self.find_best_match(bank_transaction)
            
            if best_match:
                if best_match.confidence_level in [MatchConfidence.PERFECT, MatchConfidence.HIGH]:
                    # Auto-approve high confidence matches
                    self.apply_match(best_match)
                    
                    if best_match.confidence_level == MatchConfidence.PERFECT:
                        mapping_results['perfect_matches'].append(best_match)
                    else:
                        mapping_results['high_confidence_matches'].append(best_match)
                        
                elif best_match.confidence_level == MatchConfidence.MODERATE:
                    mapping_results['moderate_matches'].append(best_match)
                    
                elif best_match.confidence_level == MatchConfidence.LOW:
                    mapping_results['low_confidence_matches'].append(best_match)
                    
                self.matches.append(best_match)
            else:
                # Create unmapped transaction entry
                unmapped_match = TransactionMatch(
                    bank_transaction_id=bank_transaction.transaction_id,
                    invoice_id=None,
                    confidence_level=MatchConfidence.UNMAPPED,
                    confidence_score=0.0,
                    mapping_factors={},
                    manual_review_required=True,
                    suggested_account=self.get_default_account(bank_transaction),
                    notes="No matching invoice found - manual mapping required"
                )
                mapping_results['unmapped_transactions'].append(unmapped_match)
                self.matches.append(unmapped_match)
        
        return mapping_results
    
    def get_default_account(self, bank_transaction: BankTransaction) -> str:
        """Get default account for unmapped transactions"""
        description_lower = bank_transaction.description.lower()
        
        # Pattern matching for common transaction types
        patterns = {
            'salary|wage|payroll': self.account_mapping_rules['salary_payment'],
            'rent|lease': self.account_mapping_rules['rent_payment'],
            'utility|electricity|water|gas': self.account_mapping_rules['utility_payment'],
            'interest|loan': self.account_mapping_rules['interest_payment'],
            'tax|gst|tds': self.account_mapping_rules['tax_payment'],
            'dividend': self.account_mapping_rules['dividend_payment']
        }
        
        for pattern, account in patterns.items():
            if re.search(pattern, description_lower):
                return account
        
        return self.account_mapping_rules['miscellaneous']
    
    def apply_match(self, match: TransactionMatch) -> bool:
        """Apply a confirmed match"""
        try:
            # Update bank transaction
            bank_transaction = next(
                (bt for bt in self.bank_transactions if bt.transaction_id == match.bank_transaction_id),
                None
            )
            if bank_transaction:
                bank_transaction.matched = True
                bank_transaction.matched_invoice_id = match.invoice_id
                bank_transaction.confidence_score = match.confidence_score
            
            # Update invoice
            if match.invoice_id:
                invoice = next(
                    (inv for inv in self.invoices if inv.invoice_id == match.invoice_id),
                    None
                )
                if invoice:
                    invoice.matched = True
                    invoice.matched_bank_transaction_id = match.bank_transaction_id
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying match: {str(e)}")
            return False
    
    def generate_reconciliation_report(self) -> Dict[str, Any]:
        """Generate comprehensive reconciliation report"""
        total_transactions = len(self.bank_transactions)
        matched_transactions = len([bt for bt in self.bank_transactions if bt.matched])
        unmapped_transactions = total_transactions - matched_transactions
        
        # Calculate amounts
        total_credits = sum(bt.amount for bt in self.bank_transactions if bt.amount > 0)
        total_debits = sum(abs(bt.amount) for bt in self.bank_transactions if bt.amount < 0)
        matched_amount = sum(bt.amount for bt in self.bank_transactions if bt.matched)
        unmapped_amount = sum(bt.amount for bt in self.bank_transactions if not bt.matched)
        
        # Generate report
        report = {
            'reconciliation_summary': {
                'total_transactions': total_transactions,
                'matched_transactions': matched_transactions,
                'unmapped_transactions': unmapped_transactions,
                'matching_percentage': (matched_transactions / total_transactions * 100) if total_transactions > 0 else 0,
                'total_credits': total_credits,
                'total_debits': total_debits,
                'matched_amount': matched_amount,
                'unmapped_amount': unmapped_amount,
                'reconciliation_date': datetime.now().isoformat()
            },
            'confidence_breakdown': {
                'perfect_matches': len([m for m in self.matches if m.confidence_level == MatchConfidence.PERFECT]),
                'high_confidence': len([m for m in self.matches if m.confidence_level == MatchConfidence.HIGH]),
                'moderate_confidence': len([m for m in self.matches if m.confidence_level == MatchConfidence.MODERATE]),
                'low_confidence': len([m for m in self.matches if m.confidence_level == MatchConfidence.LOW]),
                'unmapped': len([m for m in self.matches if m.confidence_level == MatchConfidence.UNMAPPED])
            },
            'unmapped_transactions': [
                {
                    'transaction_id': bt.transaction_id,
                    'date': bt.date.isoformat(),
                    'description': bt.description,
                    'amount': bt.amount,
                    'reference': bt.reference,
                    'suggested_account': next(
                        (m.suggested_account for m in self.matches if m.bank_transaction_id == bt.transaction_id),
                        self.get_default_account(bt)
                    )
                }
                for bt in self.bank_transactions if not bt.matched
            ],
            'matched_transactions': [
                {
                    'transaction_id': bt.transaction_id,
                    'invoice_id': bt.matched_invoice_id,
                    'confidence_score': bt.confidence_score,
                    'amount': bt.amount,
                    'date': bt.date.isoformat(),
                    'description': bt.description
                }
                for bt in self.bank_transactions if bt.matched
            ]
        }
        
        self.reconciliation_summary = report
        return report
    
    def export_reconciliation_results(self, output_path: str = "reconciliation_results.xlsx") -> bool:
        """Export reconciliation results to Excel"""
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = []
                if self.reconciliation_summary:
                    summary = self.reconciliation_summary['reconciliation_summary']
                    summary_data = [
                        ['Total Transactions', summary['total_transactions']],
                        ['Matched Transactions', summary['matched_transactions']],
                        ['Unmapped Transactions', summary['unmapped_transactions']],
                        ['Matching Percentage', f"{summary['matching_percentage']:.1f}%"],
                        ['Total Credits', f"₹{summary['total_credits']:,.2f}"],
                        ['Total Debits', f"₹{summary['total_debits']:,.2f}"],
                        ['Matched Amount', f"₹{summary['matched_amount']:,.2f}"],
                        ['Unmapped Amount', f"₹{summary['unmapped_amount']:,.2f}"]
                    ]
                
                pd.DataFrame(summary_data, columns=['Metric', 'Value']).to_excel(
                    writer, sheet_name='Summary', index=False
                )
                
                # Matched transactions sheet
                matched_data = []
                for bt in self.bank_transactions:
                    if bt.matched:
                        matched_data.append({
                            'Transaction ID': bt.transaction_id,
                            'Date': bt.date.strftime('%Y-%m-%d'),
                            'Description': bt.description,
                            'Amount': bt.amount,
                            'Reference': bt.reference,
                            'Matched Invoice': bt.matched_invoice_id,
                            'Confidence Score': f"{bt.confidence_score:.2%}"
                        })
                
                pd.DataFrame(matched_data).to_excel(
                    writer, sheet_name='Matched Transactions', index=False
                )
                
                # Unmapped transactions sheet
                unmapped_data = []
                for bt in self.bank_transactions:
                    if not bt.matched:
                        suggested_account = self.get_default_account(bt)
                        unmapped_data.append({
                            'Transaction ID': bt.transaction_id,
                            'Date': bt.date.strftime('%Y-%m-%d'),
                            'Description': bt.description,
                            'Amount': bt.amount,
                            'Reference': bt.reference,
                            'Suggested Account': suggested_account,
                            'Manual Action Required': 'Yes'
                        })
                
                pd.DataFrame(unmapped_data).to_excel(
                    writer, sheet_name='Unmapped Transactions', index=False
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting reconciliation results: {str(e)}")
            return False