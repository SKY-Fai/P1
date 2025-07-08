"""
Professional AR/AP Management Service - F-AI Accountant
Comprehensive Accounts Receivable and Accounts Payable automation with AI integration
ENHANCED: Automatic invoice template fetching and bank reconciliation integration
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid
import re
import os
import json
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvoiceStatus(Enum):
    """Invoice processing status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    PARTIALLY_PAID = "partially_paid"
    DISPUTED = "disputed"

class PaymentStatus(Enum):
    """Payment processing status"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TransactionType(Enum):
    """Transaction type classification"""
    ACCOUNTS_RECEIVABLE = "ar"
    ACCOUNTS_PAYABLE = "ap"
    BANK_RECONCILIATION = "bank_recon"
    JOURNAL_ENTRY = "journal"

@dataclass
class Invoice:
    """Invoice data structure"""
    invoice_id: str
    invoice_number: str
    invoice_type: str  # 'AR' or 'AP'
    party_name: str
    party_code: str
    invoice_date: datetime
    due_date: datetime
    amount: Decimal
    outstanding_amount: Decimal
    tax_amount: Decimal = field(default=Decimal('0'))
    discount_amount: Decimal = field(default=Decimal('0'))
    status: InvoiceStatus = field(default=InvoiceStatus.DRAFT)
    description: str = ""
    reference_number: str = ""
    payment_terms: str = ""
    fraud_score: float = field(default=0.0)
    fraud_flags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
@dataclass
class Payment:
    """Payment record structure"""
    payment_id: str
    invoice_id: str
    payment_date: datetime
    amount: Decimal
    payment_method: str
    reference_number: str
    bank_transaction_id: Optional[str] = None
    status: PaymentStatus = field(default=PaymentStatus.PENDING)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Vendor:
    """Vendor/Customer data structure"""
    party_id: str
    party_name: str
    party_type: str  # 'vendor' or 'customer'
    contact_email: str
    contact_phone: str
    address: str
    payment_terms: str
    credit_limit: Decimal = field(default=Decimal('0'))
    risk_score: float = field(default=0.0)
    created_at: datetime = field(default_factory=datetime.now)

class ARAPManagementService:
    """
    Professional AR/AP Management Service with AI integration
    """
    
    def __init__(self, company_id: int, user_id: int):
        self.company_id = company_id
        self.user_id = user_id
        
        # Data storage
        self.invoices = {}
        self.ar_invoices = {}  # Accounts Receivable invoices
        self.ap_invoices = {}  # Accounts Payable invoices
        self.payments = {}
        self.vendors = {}
        self.customers = {}
        self.reconciliation_rules = []
        
        # AI Configuration
        self.ai_categorization_enabled = True
        self.fraud_detection_enabled = True
        self.payment_prediction_enabled = True
        
        # Integration services
        self._initialize_integration_services()
        
        # Generate dummy data for testing
        self._generate_dummy_data()
        
        logger.info("AR/AP Management Service initialized successfully")
    
    def _initialize_integration_services(self):
        """Initialize integration with other services"""
        try:
            # Bank reconciliation integration
            from services.bank_reconciliation_service import BankReconciliationService
            self.bank_service = BankReconciliationService(self.company_id, self.user_id)
            
            # Manual journal integration
            from services.enhanced_manual_journal_service import EnhancedManualJournalService
            self.journal_service = EnhancedManualJournalService(self.company_id, self.user_id)
            
            # Accounting engine integration
            from services.automated_accounting_engine import AutomatedAccountingEngine
            self.accounting_engine = AutomatedAccountingEngine(self.company_id, self.user_id)
            
            logger.info("Integration services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing integration services: {str(e)}")
    
    def process_invoice_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process AR/AP invoice template with validation and AI categorization"""
        try:
            # Validate template structure
            validation_result = self._validate_invoice_template(template_data)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Extract invoice data
            invoices = self._extract_invoice_data(template_data)
            
            # AI categorization and validation
            categorized_invoices = self._ai_categorize_invoices(invoices)
            
            # Fraud detection
            fraud_checked_invoices = self._fraud_detection_check(categorized_invoices)
            
            # Process each invoice
            processed_invoices = []
            for invoice_data in fraud_checked_invoices:
                invoice = self._create_invoice_record(invoice_data)
                self.invoices[invoice.invoice_id] = invoice
                processed_invoices.append(invoice)
            
            # Generate accounting entries
            accounting_entries = self._generate_accounting_entries(processed_invoices)
            
            return {
                'success': True,
                'processed_count': len(processed_invoices),
                'ar_invoices': [inv for inv in processed_invoices if inv.invoice_type == 'AR'],
                'ap_invoices': [inv for inv in processed_invoices if inv.invoice_type == 'AP'],
                'accounting_entries': accounting_entries,
                'fraud_alerts': self._get_fraud_alerts(processed_invoices)
            }
            
        except Exception as e:
            logger.error(f"Error processing invoice template: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _validate_invoice_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate invoice template structure and required fields"""
        required_fields = [
            'invoice_number', 'party_name', 'invoice_date', 
            'due_date', 'amount', 'invoice_type'
        ]
        
        if 'invoices' not in template_data:
            return {'valid': False, 'error': 'No invoice data found in template'}
        
        invoices = template_data['invoices']
        if not isinstance(invoices, list) or len(invoices) == 0:
            return {'valid': False, 'error': 'Invalid invoice data format'}
        
        # Check required fields
        for i, invoice in enumerate(invoices):
            for field in required_fields:
                if field not in invoice or not invoice[field]:
                    return {
                        'valid': False, 
                        'error': f'Missing required field "{field}" in invoice {i+1}'
                    }
        
        return {'valid': True}
    
    def _extract_invoice_data(self, template_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and normalize invoice data from template"""
        invoices = []
        
        for invoice_data in template_data['invoices']:
            # Clean and normalize data
            normalized_invoice = {
                'invoice_number': str(invoice_data['invoice_number']).strip(),
                'party_name': str(invoice_data['party_name']).strip(),
                'invoice_type': str(invoice_data['invoice_type']).upper(),
                'invoice_date': self._parse_date(invoice_data['invoice_date']),
                'due_date': self._parse_date(invoice_data['due_date']),
                'amount': Decimal(str(invoice_data['amount'])),
                'tax_amount': Decimal(str(invoice_data.get('tax_amount', 0))),
                'discount_amount': Decimal(str(invoice_data.get('discount_amount', 0))),
                'description': str(invoice_data.get('description', '')),
                'reference_number': str(invoice_data.get('reference_number', '')),
                'payment_terms': str(invoice_data.get('payment_terms', ''))
            }
            
            invoices.append(normalized_invoice)
        
        return invoices
    
    def _ai_categorize_invoices(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """AI-powered invoice categorization and GL code prediction"""
        if not self.ai_categorization_enabled:
            return invoices
        
        categorized_invoices = []
        
        for invoice in invoices:
            # AI categorization based on description and party name
            category = self._predict_expense_category(invoice['description'], invoice['party_name'])
            gl_code = self._predict_gl_code(category, invoice['invoice_type'])
            
            # Add AI predictions
            invoice['ai_category'] = category
            invoice['predicted_gl_code'] = gl_code
            invoice['ai_confidence'] = self._calculate_ai_confidence(invoice)
            
            categorized_invoices.append(invoice)
        
        return categorized_invoices
    
    def _predict_expense_category(self, description: str, party_name: str) -> str:
        """Predict expense category using AI pattern matching"""
        description_lower = description.lower()
        party_lower = party_name.lower()
        
        # Pattern matching rules
        if any(keyword in description_lower for keyword in ['rent', 'lease', 'office space']):
            return 'Rent & Utilities'
        elif any(keyword in description_lower for keyword in ['salary', 'wages', 'payroll']):
            return 'Payroll'
        elif any(keyword in description_lower for keyword in ['office supplies', 'stationery']):
            return 'Office Supplies'
        elif any(keyword in description_lower for keyword in ['travel', 'transport', 'fuel']):
            return 'Travel & Transportation'
        elif any(keyword in description_lower for keyword in ['marketing', 'advertising', 'promotion']):
            return 'Marketing & Advertising'
        elif any(keyword in description_lower for keyword in ['professional', 'consultant', 'legal']):
            return 'Professional Services'
        elif any(keyword in description_lower for keyword in ['software', 'license', 'subscription']):
            return 'Software & Technology'
        else:
            return 'General Expenses'
    
    def _predict_gl_code(self, category: str, invoice_type: str) -> str:
        """Predict GL code based on category and invoice type"""
        gl_codes = {
            'AR': {
                'Sales Revenue': '4000',
                'Service Revenue': '4100',
                'Interest Income': '4200',
                'Other Revenue': '4900'
            },
            'AP': {
                'Rent & Utilities': '5100',
                'Payroll': '5200',
                'Office Supplies': '5300',
                'Travel & Transportation': '5400',
                'Marketing & Advertising': '5500',
                'Professional Services': '5600',
                'Software & Technology': '5700',
                'General Expenses': '5800'
            }
        }
        
        return gl_codes.get(invoice_type, {}).get(category, '5999')
    
    def _calculate_ai_confidence(self, invoice: Dict[str, Any]) -> float:
        """Calculate AI prediction confidence score"""
        confidence = 0.8  # Base confidence
        
        # Adjust based on data quality
        if invoice['description'] and len(invoice['description']) > 10:
            confidence += 0.1
        if invoice['reference_number']:
            confidence += 0.05
        if invoice['amount'] > 0:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _fraud_detection_check(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fraud detection and anomaly analysis"""
        if not self.fraud_detection_enabled:
            return invoices
        
        for invoice in invoices:
            fraud_score = 0.0
            fraud_flags = []
            
            # Check for duplicate invoices
            if self._check_duplicate_invoice(invoice):
                fraud_score += 0.3
                fraud_flags.append('DUPLICATE_INVOICE')
            
            # Check for unusual amounts
            if self._check_unusual_amount(invoice):
                fraud_score += 0.2
                fraud_flags.append('UNUSUAL_AMOUNT')
            
            # Check for suspicious vendor patterns
            if self._check_suspicious_vendor(invoice):
                fraud_score += 0.4
                fraud_flags.append('SUSPICIOUS_VENDOR')
            
            # Check for date anomalies
            if self._check_date_anomalies(invoice):
                fraud_score += 0.1
                fraud_flags.append('DATE_ANOMALY')
            
            invoice['fraud_score'] = fraud_score
            invoice['fraud_flags'] = fraud_flags
            invoice['requires_review'] = fraud_score > 0.5
        
        return invoices
    
    def _check_duplicate_invoice(self, invoice: Dict[str, Any]) -> bool:
        """Check for duplicate invoices"""
        for existing_invoice in self.invoices.values():
            if (existing_invoice.invoice_number == invoice['invoice_number'] and
                existing_invoice.party_name == invoice['party_name']):
                return True
        return False
    
    def _check_unusual_amount(self, invoice: Dict[str, Any]) -> bool:
        """Check for unusual invoice amounts"""
        amount = float(invoice['amount'])
        
        # Check for very large amounts (> 1 million)
        if amount > 1000000:
            return True
        
        # Check for round numbers that might be suspicious
        if amount > 10000 and amount % 10000 == 0:
            return True
        
        return False
    
    def _check_suspicious_vendor(self, invoice: Dict[str, Any]) -> bool:
        """Check for suspicious vendor patterns"""
        party_name = invoice['party_name'].lower()
        
        # Check for generic names
        suspicious_patterns = ['test', 'sample', 'dummy', 'temp', 'xyz', 'abc']
        return any(pattern in party_name for pattern in suspicious_patterns)
    
    def _check_date_anomalies(self, invoice: Dict[str, Any]) -> bool:
        """Check for date anomalies"""
        invoice_date = invoice['invoice_date']
        due_date = invoice['due_date']
        
        # Check if due date is before invoice date
        if due_date < invoice_date:
            return True
        
        # Check if invoice date is too far in future
        if invoice_date > datetime.now() + timedelta(days=30):
            return True
        
        return False
    
    def _create_invoice_record(self, invoice_data: Dict[str, Any]) -> Invoice:
        """Create invoice record from processed data"""
        invoice = Invoice(
            invoice_id=str(uuid.uuid4()),
            invoice_number=invoice_data['invoice_number'],
            invoice_type=invoice_data['invoice_type'],
            party_name=invoice_data['party_name'],
            party_code=invoice_data.get('party_code', ''),
            invoice_date=invoice_data['invoice_date'],
            due_date=invoice_data['due_date'],
            amount=invoice_data['amount'],
            outstanding_amount=invoice_data['amount'],  # Initially full amount
            tax_amount=invoice_data.get('tax_amount', Decimal('0')),
            discount_amount=invoice_data.get('discount_amount', Decimal('0')),
            description=invoice_data.get('description', ''),
            reference_number=invoice_data.get('reference_number', ''),
            payment_terms=invoice_data.get('payment_terms', '')
        )
        
        return invoice
    
    def _generate_accounting_entries(self, invoices: List[Invoice]) -> List[Dict[str, Any]]:
        """Generate accounting entries for processed invoices"""
        accounting_entries = []
        
        for invoice in invoices:
            if invoice.invoice_type == 'AR':
                # Accounts Receivable entry
                entry = {
                    'entry_id': f"AR_{invoice.invoice_id}",
                    'date': invoice.invoice_date.strftime('%Y-%m-%d'),
                    'description': f"Sales Invoice - {invoice.invoice_number}",
                    'reference': invoice.invoice_number,
                    'entries': [
                        {
                            'account_code': '1200',  # Accounts Receivable
                            'debit_amount': float(invoice.amount),
                            'credit_amount': 0.0,
                            'description': f"AR - {invoice.party_name}"
                        },
                        {
                            'account_code': '4000',  # Sales Revenue
                            'debit_amount': 0.0,
                            'credit_amount': float(invoice.amount),
                            'description': f"Sales - {invoice.party_name}"
                        }
                    ]
                }
            else:  # AP
                # Accounts Payable entry
                entry = {
                    'entry_id': f"AP_{invoice.invoice_id}",
                    'date': invoice.invoice_date.strftime('%Y-%m-%d'),
                    'description': f"Purchase Invoice - {invoice.invoice_number}",
                    'reference': invoice.invoice_number,
                    'entries': [
                        {
                            'account_code': '5000',  # Expenses
                            'debit_amount': float(invoice.amount),
                            'credit_amount': 0.0,
                            'description': f"Expense - {invoice.party_name}"
                        },
                        {
                            'account_code': '2100',  # Accounts Payable
                            'debit_amount': 0.0,
                            'credit_amount': float(invoice.amount),
                            'description': f"AP - {invoice.party_name}"
                        }
                    ]
                }
            
            accounting_entries.append(entry)
        
        return accounting_entries
    
    def _get_fraud_alerts(self, invoices: List[Invoice]) -> List[Dict[str, Any]]:
        """Get fraud alerts for processed invoices"""
        alerts = []
        
        for invoice in invoices:
            if hasattr(invoice, 'fraud_score') and invoice.fraud_score > 0.5:
                alerts.append({
                    'invoice_id': invoice.invoice_id,
                    'invoice_number': invoice.invoice_number,
                    'party_name': invoice.party_name,
                    'fraud_score': invoice.fraud_score,
                    'fraud_flags': invoice.fraud_flags,
                    'alert_level': 'HIGH' if invoice.fraud_score > 0.7 else 'MEDIUM'
                })
        
        return alerts
    
    def _parse_date(self, date_input: Any) -> datetime:
        """Parse date from various input formats"""
        if isinstance(date_input, datetime):
            return date_input
        
        if isinstance(date_input, str):
            # Try various date formats
            formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_input, fmt)
                except ValueError:
                    continue
        
        # Default to current date if parsing fails
        return datetime.now()
    
    def get_ar_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive AR dashboard data"""
        ar_invoices = [inv for inv in self.invoices.values() if inv.invoice_type == 'AR']
        
        # Calculate metrics
        total_outstanding = sum(inv.outstanding_amount for inv in ar_invoices)
        overdue_invoices = [inv for inv in ar_invoices if inv.due_date < datetime.now()]
        overdue_amount = sum(inv.outstanding_amount for inv in overdue_invoices)
        
        # Aging analysis
        aging_buckets = self._calculate_aging_buckets(ar_invoices)
        
        # Payment predictions
        payment_predictions = self._predict_payment_dates(ar_invoices)
        
        return {
            'total_invoices': len(ar_invoices),
            'total_outstanding': float(total_outstanding),
            'overdue_count': len(overdue_invoices),
            'overdue_amount': float(overdue_amount),
            'aging_buckets': aging_buckets,
            'payment_predictions': payment_predictions,
            'recent_invoices': self._get_recent_invoices(ar_invoices, 10)
        }
    
    def get_ap_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive AP dashboard data"""
        ap_invoices = [inv for inv in self.invoices.values() if inv.invoice_type == 'AP']
        
        # Calculate metrics
        total_outstanding = sum(inv.outstanding_amount for inv in ap_invoices)
        due_soon = [inv for inv in ap_invoices if inv.due_date <= datetime.now() + timedelta(days=7)]
        due_soon_amount = sum(inv.outstanding_amount for inv in due_soon)
        
        # Aging analysis
        aging_buckets = self._calculate_aging_buckets(ap_invoices)
        
        # Payment schedule
        payment_schedule = self._generate_payment_schedule(ap_invoices)
        
        return {
            'total_invoices': len(ap_invoices),
            'total_outstanding': float(total_outstanding),
            'due_soon_count': len(due_soon),
            'due_soon_amount': float(due_soon_amount),
            'aging_buckets': aging_buckets,
            'payment_schedule': payment_schedule,
            'recent_invoices': self._get_recent_invoices(ap_invoices, 10)
        }
    
    def _calculate_aging_buckets(self, invoices: List[Invoice]) -> Dict[str, Any]:
        """Calculate aging buckets for invoices"""
        buckets = {
            'current': 0,
            '1-30': 0,
            '31-60': 0,
            '61-90': 0,
            '90+': 0
        }
        
        now = datetime.now()
        
        for invoice in invoices:
            days_overdue = (now - invoice.due_date).days
            amount = float(invoice.outstanding_amount)
            
            if days_overdue <= 0:
                buckets['current'] += amount
            elif days_overdue <= 30:
                buckets['1-30'] += amount
            elif days_overdue <= 60:
                buckets['31-60'] += amount
            elif days_overdue <= 90:
                buckets['61-90'] += amount
            else:
                buckets['90+'] += amount
        
        return buckets
    
    def _predict_payment_dates(self, invoices: List[Invoice]) -> List[Dict[str, Any]]:
        """Predict payment dates using AI"""
        predictions = []
        
        for invoice in invoices:
            # Simple prediction based on payment terms and historical data
            predicted_date = self._calculate_predicted_payment_date(invoice)
            confidence = self._calculate_prediction_confidence(invoice)
            
            predictions.append({
                'invoice_id': invoice.invoice_id,
                'invoice_number': invoice.invoice_number,
                'party_name': invoice.party_name,
                'amount': float(invoice.outstanding_amount),
                'predicted_date': predicted_date.strftime('%Y-%m-%d'),
                'confidence': confidence
            })
        
        return predictions
    
    def _calculate_predicted_payment_date(self, invoice: Invoice) -> datetime:
        """Calculate predicted payment date"""
        # Simple prediction: due date + average delay
        average_delay = 5  # days
        return invoice.due_date + timedelta(days=average_delay)
    
    def _calculate_prediction_confidence(self, invoice: Invoice) -> float:
        """Calculate prediction confidence"""
        # Base confidence depends on payment terms and amount
        confidence = 0.7
        
        if invoice.payment_terms:
            confidence += 0.1
        if invoice.outstanding_amount < 10000:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_payment_schedule(self, invoices: List[Invoice]) -> List[Dict[str, Any]]:
        """Generate payment schedule for AP invoices"""
        schedule = []
        
        for invoice in invoices:
            if invoice.outstanding_amount > 0:
                schedule.append({
                    'invoice_id': invoice.invoice_id,
                    'invoice_number': invoice.invoice_number,
                    'party_name': invoice.party_name,
                    'amount': float(invoice.outstanding_amount),
                    'due_date': invoice.due_date.strftime('%Y-%m-%d'),
                    'days_until_due': (invoice.due_date - datetime.now()).days,
                    'priority': self._calculate_payment_priority(invoice)
                })
        
        # Sort by due date
        schedule.sort(key=lambda x: x['due_date'])
        
        return schedule
    
    def _calculate_payment_priority(self, invoice: Invoice) -> str:
        """Calculate payment priority"""
        days_until_due = (invoice.due_date - datetime.now()).days
        
        if days_until_due < 0:
            return 'OVERDUE'
        elif days_until_due <= 3:
            return 'URGENT'
        elif days_until_due <= 7:
            return 'HIGH'
        elif days_until_due <= 14:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_recent_invoices(self, invoices: List[Invoice], limit: int) -> List[Dict[str, Any]]:
        """Get recent invoices for dashboard"""
        sorted_invoices = sorted(invoices, key=lambda x: x.created_at, reverse=True)
        
        recent = []
        for invoice in sorted_invoices[:limit]:
            recent.append({
                'invoice_id': invoice.invoice_id,
                'invoice_number': invoice.invoice_number,
                'party_name': invoice.party_name,
                'amount': float(invoice.amount),
                'outstanding_amount': float(invoice.outstanding_amount),
                'due_date': invoice.due_date.strftime('%Y-%m-%d'),
                'status': invoice.status.value,
                'created_at': invoice.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return recent
    
    def bank_reconciliation_integration(self, bank_transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Integrate with bank reconciliation for automatic payment matching"""
        try:
            matched_payments = []
            unmatched_transactions = []
            
            for transaction in bank_transactions:
                # Try to match with outstanding invoices
                match_result = self._match_transaction_to_invoice(transaction)
                
                if match_result['matched']:
                    # Create payment record
                    payment = self._create_payment_record(transaction, match_result['invoice'])
                    matched_payments.append(payment)
                    
                    # Update invoice status
                    self._update_invoice_payment_status(match_result['invoice'], payment)
                else:
                    unmatched_transactions.append(transaction)
            
            return {
                'success': True,
                'matched_payments': len(matched_payments),
                'unmatched_transactions': len(unmatched_transactions),
                'payment_records': matched_payments,
                'unmatched_data': unmatched_transactions
            }
            
        except Exception as e:
            logger.error(f"Error in bank reconciliation integration: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _match_transaction_to_invoice(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Match bank transaction to outstanding invoice"""
        transaction_amount = abs(float(transaction.get('amount', 0)))
        transaction_desc = transaction.get('description', '').lower()
        
        # Search for matching invoices
        for invoice in self.invoices.values():
            if invoice.outstanding_amount == 0:
                continue
            
            # Amount matching
            if abs(float(invoice.outstanding_amount) - transaction_amount) < 0.01:
                # Check description matching
                if (invoice.invoice_number.lower() in transaction_desc or
                    invoice.party_name.lower() in transaction_desc):
                    return {
                        'matched': True,
                        'invoice': invoice,
                        'confidence': 0.95
                    }
        
        return {'matched': False}
    
    def _create_payment_record(self, transaction: Dict[str, Any], invoice: Invoice) -> Payment:
        """Create payment record from matched transaction"""
        payment = Payment(
            payment_id=str(uuid.uuid4()),
            invoice_id=invoice.invoice_id,
            payment_date=transaction.get('date', datetime.now()),
            amount=Decimal(str(abs(float(transaction.get('amount', 0))))),
            payment_method=transaction.get('method', 'Bank Transfer'),
            reference_number=transaction.get('reference', ''),
            bank_transaction_id=transaction.get('transaction_id'),
            status=PaymentStatus.COMPLETED
        )
        
        self.payments[payment.payment_id] = payment
        return payment
    
    def _update_invoice_payment_status(self, invoice: Invoice, payment: Payment):
        """Update invoice payment status"""
        invoice.outstanding_amount -= payment.amount
        
        if invoice.outstanding_amount <= 0:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        
        invoice.updated_at = datetime.now()
    
    def _generate_dummy_data(self):
        """Generate dummy data for testing AR/AP functionality"""
        try:
            # Create dummy vendors
            vendors = [
                Vendor(
                    party_id="V001",
                    party_name="ABC Office Supplies",
                    party_type="vendor",
                    contact_email="billing@abcoffice.com",
                    contact_phone="+91-9876543210",
                    address="123 Business Park, Mumbai, MH 400001",
                    payment_terms="Net 30",
                    credit_limit=Decimal('100000')
                ),
                Vendor(
                    party_id="V002",
                    party_name="XYZ Tech Solutions",
                    party_type="vendor",
                    contact_email="accounts@xyztech.com",
                    contact_phone="+91-9876543211",
                    address="456 Tech Hub, Pune, MH 411001",
                    payment_terms="Net 15",
                    credit_limit=Decimal('200000')
                ),
                Vendor(
                    party_id="V003",
                    party_name="Global Logistics Co",
                    party_type="vendor",
                    contact_email="payables@globallogistics.com",
                    contact_phone="+91-9876543212",
                    address="789 Transport Nagar, Delhi, DL 110001",
                    payment_terms="Net 45",
                    credit_limit=Decimal('150000')
                )
            ]
            
            # Create dummy customers
            customers = [
                Vendor(
                    party_id="C001",
                    party_name="Acme Corp",
                    party_type="customer",
                    contact_email="ar@acmecorp.com",
                    contact_phone="+91-9876543220",
                    address="321 Corporate Ave, Bangalore, KA 560001",
                    payment_terms="Net 30",
                    credit_limit=Decimal('500000')
                ),
                Vendor(
                    party_id="C002",
                    party_name="Beta Industries",
                    party_type="customer",
                    contact_email="finance@betaindustries.com",
                    contact_phone="+91-9876543221",
                    address="654 Industrial Zone, Chennai, TN 600001",
                    payment_terms="Net 15",
                    credit_limit=Decimal('300000')
                ),
                Vendor(
                    party_id="C003",
                    party_name="Gamma Solutions",
                    party_type="customer",
                    contact_email="billing@gammasolutions.com",
                    contact_phone="+91-9876543222",
                    address="987 Business District, Hyderabad, TS 500001",
                    payment_terms="Net 45",
                    credit_limit=Decimal('750000')
                )
            ]
            
            # Store vendors and customers
            for vendor in vendors:
                self.vendors[vendor.party_id] = vendor
            for customer in customers:
                self.customers[customer.party_id] = customer
            
            # Create dummy AR invoices
            ar_invoices = [
                Invoice(
                    invoice_id="AR001",
                    invoice_number="INV-2025-001",
                    invoice_type="AR",
                    party_name="Acme Corp",
                    party_code="C001",
                    invoice_date=datetime(2025, 1, 1),
                    due_date=datetime(2025, 1, 31),
                    amount=Decimal('125000'),
                    outstanding_amount=Decimal('125000'),
                    tax_amount=Decimal('22500'),
                    status=InvoiceStatus.APPROVED,
                    description="Consulting Services - Q4 2024",
                    reference_number="REF-C001-001"
                ),
                Invoice(
                    invoice_id="AR002",
                    invoice_number="INV-2025-002",
                    invoice_type="AR",
                    party_name="Beta Industries",
                    party_code="C002",
                    invoice_date=datetime(2025, 1, 5),
                    due_date=datetime(2025, 1, 20),
                    amount=Decimal('85000'),
                    outstanding_amount=Decimal('85000'),
                    tax_amount=Decimal('15300'),
                    status=InvoiceStatus.OVERDUE,
                    description="Software Development Services",
                    reference_number="REF-C002-001"
                ),
                Invoice(
                    invoice_id="AR003",
                    invoice_number="INV-2025-003",
                    invoice_type="AR",
                    party_name="Gamma Solutions",
                    party_code="C003",
                    invoice_date=datetime(2025, 1, 10),
                    due_date=datetime(2025, 2, 24),
                    amount=Decimal('275000'),
                    outstanding_amount=Decimal('175000'),
                    tax_amount=Decimal('49500'),
                    status=InvoiceStatus.PARTIALLY_PAID,
                    description="Enterprise Solution Implementation",
                    reference_number="REF-C003-001"
                )
            ]
            
            # Create dummy AP invoices
            ap_invoices = [
                Invoice(
                    invoice_id="AP001",
                    invoice_number="PO-2025-001",
                    invoice_type="AP",
                    party_name="ABC Office Supplies",
                    party_code="V001",
                    invoice_date=datetime(2025, 1, 2),
                    due_date=datetime(2025, 2, 1),
                    amount=Decimal('45000'),
                    outstanding_amount=Decimal('45000'),
                    tax_amount=Decimal('8100'),
                    status=InvoiceStatus.APPROVED,
                    description="Office Furniture & Supplies",
                    reference_number="PO-V001-001"
                ),
                Invoice(
                    invoice_id="AP002",
                    invoice_number="PO-2025-002",
                    invoice_type="AP",
                    party_name="XYZ Tech Solutions",
                    party_code="V002",
                    invoice_date=datetime(2025, 1, 8),
                    due_date=datetime(2025, 1, 23),
                    amount=Decimal('95000'),
                    outstanding_amount=Decimal('95000'),
                    tax_amount=Decimal('17100'),
                    status=InvoiceStatus.APPROVED,
                    description="IT Infrastructure Setup",
                    reference_number="PO-V002-001"
                ),
                Invoice(
                    invoice_id="AP003",
                    invoice_number="PO-2025-003",
                    invoice_type="AP",
                    party_name="Global Logistics Co",
                    party_code="V003",
                    invoice_date=datetime(2025, 1, 12),
                    due_date=datetime(2025, 2, 26),
                    amount=Decimal('65000'),
                    outstanding_amount=Decimal('65000'),
                    tax_amount=Decimal('11700'),
                    status=InvoiceStatus.APPROVED,
                    description="Shipping & Logistics Services",
                    reference_number="PO-V003-001"
                )
            ]
            
            # Store invoices
            for invoice in ar_invoices + ap_invoices:
                self.invoices[invoice.invoice_id] = invoice
            
            # Create dummy payments
            payments = [
                Payment(
                    payment_id="PAY001",
                    invoice_id="AR003",
                    payment_date=datetime(2025, 1, 15),
                    amount=Decimal('100000'),
                    payment_method="Bank Transfer",
                    reference_number="TXN-2025-001",
                    status=PaymentStatus.COMPLETED
                )
            ]
            
            for payment in payments:
                self.payments[payment.payment_id] = payment
            
            logger.info(f"Generated dummy data: {len(ar_invoices)} AR invoices, {len(ap_invoices)} AP invoices, {len(vendors)} vendors, {len(customers)} customers")
            
        except Exception as e:
            logger.error(f"Error generating dummy data: {str(e)}")
            # Continue without dummy data if there's an error
    
    def fetch_uploaded_invoice_templates(self) -> Dict[str, Any]:
        """
        Automatically fetch uploaded invoice templates from the accounting system
        """
        try:
            logger.info("Fetching uploaded invoice templates from accounting system...")
            
            # Look for uploaded files in standard upload directories
            upload_directories = [
                'uploads',
                'uploads_input', 
                'template_test_files',
                'test_data'
            ]
            
            invoice_templates = []
            processed_files = []
            
            for upload_dir in upload_directories:
                if os.path.exists(upload_dir):
                    for filename in os.listdir(upload_dir):
                        if filename.endswith(('.xlsx', '.xls', '.csv')):
                            file_path = os.path.join(upload_dir, filename)
                            
                            # Try to read and extract invoice data
                            template_data = self._extract_invoice_template_data(file_path)
                            if template_data and template_data.get('invoices'):
                                invoice_templates.extend(template_data['invoices'])
                                processed_files.append({
                                    'filename': filename,
                                    'path': file_path,
                                    'invoice_count': len(template_data['invoices']),
                                    'processed_at': datetime.now().isoformat()
                                })
            
            # Process and categorize the fetched templates
            if invoice_templates:
                processed_invoices = self._process_fetched_templates(invoice_templates)
                
                # Auto-add to AR/AP systems
                ar_count, ap_count = self._auto_add_to_ar_ap_systems(processed_invoices)
                
                return {
                    'success': True,
                    'templates_found': len(invoice_templates),
                    'files_processed': processed_files,
                    'ar_invoices_added': ar_count,
                    'ap_invoices_added': ap_count,
                    'processed_invoices': processed_invoices
                }
            else:
                return {
                    'success': True,
                    'templates_found': 0,
                    'message': 'No invoice templates found in upload directories'
                }
                
        except Exception as e:
            logger.error(f"Error fetching uploaded invoice templates: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_invoice_template_data(self, file_path: str) -> Dict[str, Any]:
        """Extract invoice data from uploaded template files"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, sheet_name=0)
            
            # Look for invoice-related columns
            invoice_columns = {
                'invoice_number': ['invoice_number', 'invoice_no', 'bill_no', 'reference_no'],
                'party_name': ['party_name', 'customer_name', 'vendor_name', 'supplier_name'],
                'amount': ['amount', 'total_amount', 'gross_amount', 'net_amount'],
                'invoice_date': ['invoice_date', 'date', 'bill_date'],
                'due_date': ['due_date', 'payment_date', 'payment_due'],
                'invoice_type': ['invoice_type', 'transaction_type', 'type']
            }
            
            # Find matching columns
            column_mapping = {}
            for required_field, possible_names in invoice_columns.items():
                for col in df.columns:
                    if col.lower().strip() in [name.lower() for name in possible_names]:
                        column_mapping[required_field] = col
                        break
            
            if not column_mapping.get('invoice_number') or not column_mapping.get('party_name'):
                return None
            
            invoices = []
            for _, row in df.iterrows():
                if pd.isna(row.get(column_mapping.get('invoice_number'))):
                    continue
                    
                invoice = {
                    'invoice_number': str(row[column_mapping['invoice_number']]).strip(),
                    'party_name': str(row[column_mapping['party_name']]).strip(),
                    'amount': float(row.get(column_mapping.get('amount'), 0)),
                    'invoice_date': row.get(column_mapping.get('invoice_date'), datetime.now()),
                    'due_date': row.get(column_mapping.get('due_date'), datetime.now() + timedelta(days=30)),
                    'invoice_type': str(row.get(column_mapping.get('invoice_type'), 'AR')).upper()
                }
                invoices.append(invoice)
            
            return {
                'invoices': invoices,
                'source_file': file_path,
                'columns_found': column_mapping
            }
            
        except Exception as e:
            logger.error(f"Error extracting template data from {file_path}: {str(e)}")
            return None
    
    def _process_fetched_templates(self, invoice_templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and enhance fetched invoice templates"""
        processed = []
        
        for invoice in invoice_templates:
            # Enhanced processing with AI categorization
            processed_invoice = {
                'invoice_id': str(uuid.uuid4()),
                'invoice_number': invoice['invoice_number'],
                'party_name': invoice['party_name'],
                'amount': Decimal(str(invoice['amount'])),
                'outstanding_amount': Decimal(str(invoice['amount'])),  # Initially full amount
                'invoice_date': invoice['invoice_date'],
                'due_date': invoice['due_date'],
                'invoice_type': invoice.get('invoice_type', 'AR'),
                'status': InvoiceStatus.APPROVED.value,
                'auto_fetched': True,
                'processed_at': datetime.now().isoformat(),
                'description': f"Auto-fetched from template: {invoice.get('description', '')}",
                'reference_number': invoice.get('reference_number', '')
            }
            
            # AI categorization for AP invoices
            if processed_invoice['invoice_type'] == 'AP':
                processed_invoice['expense_category'] = self._predict_expense_category(
                    processed_invoice['description'], 
                    processed_invoice['party_name']
                )
            
            processed.append(processed_invoice)
        
        return processed
    
    def _auto_add_to_ar_ap_systems(self, processed_invoices: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Automatically add processed invoices to AR/AP systems"""
        ar_count = 0
        ap_count = 0
        
        for invoice in processed_invoices:
            if invoice['invoice_type'] == 'AR':
                # Add to AR system
                ar_invoice = Invoice(
                    invoice_id=invoice['invoice_id'],
                    invoice_number=invoice['invoice_number'],
                    invoice_type='AR',
                    party_name=invoice['party_name'],
                    party_code=invoice.get('party_code', f"CUST{invoice['invoice_id'][:6]}"),
                    amount=invoice['amount'],
                    outstanding_amount=invoice['outstanding_amount'],
                    invoice_date=invoice['invoice_date'],
                    due_date=invoice['due_date'],
                    status=InvoiceStatus.APPROVED,
                    description=invoice['description'],
                    reference_number=invoice['reference_number']
                )
                self.ar_invoices[invoice['invoice_id']] = ar_invoice
                ar_count += 1
                
            elif invoice['invoice_type'] == 'AP':
                # Add to AP system
                ap_invoice = Invoice(
                    invoice_id=invoice['invoice_id'],
                    invoice_number=invoice['invoice_number'],
                    invoice_type='AP',
                    party_name=invoice['party_name'],
                    party_code=invoice.get('party_code', f"VEND{invoice['invoice_id'][:6]}"),
                    amount=invoice['amount'],
                    outstanding_amount=invoice['outstanding_amount'],
                    invoice_date=invoice['invoice_date'],
                    due_date=invoice['due_date'],
                    status=InvoiceStatus.APPROVED,
                    description=invoice['description'],
                    reference_number=invoice['reference_number']
                )
                self.ap_invoices[invoice['invoice_id']] = ap_invoice
                ap_count += 1
        
        return ar_count, ap_count
    
    def trigger_bank_reconciliation_integration(self, bank_statement_path: str) -> Dict[str, Any]:
        """
        Automatically trigger bank reconciliation when bank statement is uploaded
        Integrates AR/AP data with bank reconciliation for complete workflow
        """
        try:
            logger.info("Triggering automatic bank reconciliation with AR/AP integration...")
            
            # First, fetch any new invoice templates
            template_fetch_result = self.fetch_uploaded_invoice_templates()
            
            # Get current AR/AP data for reconciliation
            ar_data = self.get_ar_dashboard_data()
            ap_data = self.get_ap_dashboard_data()
            
            # Prepare integration data for bank reconciliation
            integration_data = {
                'ar_invoices': [
                    {
                        'invoice_number': inv.invoice_number,
                        'party_name': inv.party_name,
                        'amount': float(inv.outstanding_amount),
                        'due_date': inv.due_date.isoformat() if inv.due_date else None,
                        'reference_number': inv.reference_number,
                        'type': 'receivable'
                    }
                    for inv in self.ar_invoices.values()
                ],
                'ap_invoices': [
                    {
                        'invoice_number': inv.invoice_number,
                        'party_name': inv.party_name,
                        'amount': float(inv.outstanding_amount),
                        'due_date': inv.due_date.isoformat() if inv.due_date else None,
                        'reference_number': inv.reference_number,
                        'type': 'payable'
                    }
                    for inv in self.ap_invoices.values()
                ],
                'template_fetch_result': template_fetch_result,
                'ar_summary': ar_data.get('dashboard', {}),
                'ap_summary': ap_data.get('dashboard', {})
            }
            
            # Save integration data for bank reconciliation to use
            integration_file = 'ar_ap_integration_data.json'
            with open(integration_file, 'w') as f:
                json.dump(integration_data, f, indent=2, default=str)
            
            return {
                'success': True,
                'message': 'Bank reconciliation integration triggered successfully',
                'ar_invoices_count': len(integration_data['ar_invoices']),
                'ap_invoices_count': len(integration_data['ap_invoices']),
                'integration_file': integration_file,
                'template_fetch_result': template_fetch_result
            }
            
        except Exception as e:
            logger.error(f"Error triggering bank reconciliation integration: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }