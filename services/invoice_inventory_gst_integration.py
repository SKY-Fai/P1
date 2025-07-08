"""
Invoice Inventory & GST Portal Integration with Automated Journal Generation
Seamless integration between Invoice Management, Inventory Tracking, GST Portal, and Automated Accounting Engine
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid
import json
import pandas as pd
import os

from services.automated_accounting_engine import AutomatedAccountingEngine
from services.ar_ap_management_service import ARAPManagementService, Invoice, InvoiceStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """Types of integration workflows"""
    INVOICE_TO_JOURNAL = "invoice_to_journal"
    INVENTORY_TO_JOURNAL = "inventory_to_journal"
    GST_TO_JOURNAL = "gst_to_journal"
    COMBINED_WORKFLOW = "combined_workflow"

class TransactionCategory(Enum):
    """Enhanced transaction categorization"""
    SALES_INVOICE = "sales_invoice"
    PURCHASE_INVOICE = "purchase_invoice"
    INVENTORY_ADJUSTMENT = "inventory_adjustment"
    GST_PAYMENT = "gst_payment"
    GST_RECEIPT = "gst_receipt"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"

@dataclass
class IntegratedTransaction:
    """Comprehensive transaction structure for integration"""
    transaction_id: str
    transaction_type: TransactionCategory
    invoice_data: Optional[Dict[str, Any]] = None
    inventory_data: Optional[Dict[str, Any]] = None
    gst_data: Optional[Dict[str, Any]] = None
    journal_entries: List[Dict[str, Any]] = field(default_factory=list)
    integration_timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    amount_total: Decimal = field(default=Decimal('0'))
    tax_amount: Decimal = field(default=Decimal('0'))

class InvoiceInventoryGSTIntegration:
    """
    Comprehensive integration service for Invoice Management, Inventory Tracking, 
    GST Portal, and Automated Journal Generation
    """
    
    def __init__(self, company_id: int = 1, user_id: int = 1):
        self.company_id = company_id
        self.user_id = user_id
        self.accounting_engine = AutomatedAccountingEngine(company_id, user_id)
        self.ar_ap_service = ARAPManagementService(company_id, user_id)
        self.integrated_transactions = {}
        
        # Initialize integration mappings
        self.account_mappings = self._initialize_account_mappings()
        self.gst_account_mappings = self._initialize_gst_mappings()
        self.inventory_mappings = self._initialize_inventory_mappings()
    
    def _initialize_account_mappings(self) -> Dict[str, str]:
        """Initialize account mappings for different transaction types"""
        return {
            # Sales Invoice Accounts
            'sales_revenue': '4000',
            'accounts_receivable': '1100',
            'sales_tax_payable': '2220',
            'cash_account': '1000',
            
            # Purchase Invoice Accounts
            'purchase_expense': '5000',
            'accounts_payable': '2010',
            'purchase_tax_receivable': '1150',
            'inventory_account': '1200',
            
            # Inventory Accounts
            'raw_materials': '1210',
            'finished_goods': '1230',
            'work_in_progress': '1220',
            'cost_of_goods_sold': '5100',
            
            # GST Accounts
            'gst_input_credit': '1160',
            'gst_output_liability': '2220',
            'gst_payment_account': '1000'
        }
    
    def _initialize_gst_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize GST-specific account mappings"""
        return {
            'CGST': {
                'input': '1161',  # CGST Input Credit
                'output': '2221', # CGST Output Liability
                'payment': '1000' # Cash/Bank for GST Payment
            },
            'SGST': {
                'input': '1162',  # SGST Input Credit
                'output': '2222', # SGST Output Liability
                'payment': '1000'
            },
            'IGST': {
                'input': '1163',  # IGST Input Credit
                'output': '2223', # IGST Output Liability
                'payment': '1000'
            }
        }
    
    def _initialize_inventory_mappings(self) -> Dict[str, str]:
        """Initialize inventory-specific mappings"""
        return {
            'purchase_to_inventory': {
                'debit_account': '1200',  # Inventory
                'credit_account': '2010'  # Accounts Payable
            },
            'inventory_to_sales': {
                'debit_account': '5100',  # Cost of Goods Sold
                'credit_account': '1200'  # Inventory
            },
            'inventory_adjustment': {
                'debit_account': '1200',  # Inventory (if increase)
                'credit_account': '5150'  # Inventory Adjustment Expense
            }
        }
    
    def process_sales_invoice_integration(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sales invoice with automatic inventory reduction and GST calculation
        """
        try:
            logger.info(f"Processing sales invoice integration: {invoice_data.get('invoice_number')}")
            
            transaction_id = str(uuid.uuid4())
            
            # Create integrated transaction
            integrated_transaction = IntegratedTransaction(
                transaction_id=transaction_id,
                transaction_type=TransactionCategory.SALES_INVOICE,
                invoice_data=invoice_data
            )
            
            # Step 1: Process sales invoice journal entries
            sales_entries = self._create_sales_journal_entries(invoice_data)
            integrated_transaction.journal_entries.extend(sales_entries)
            
            # Step 2: Process inventory reduction (if applicable)
            if invoice_data.get('inventory_items'):
                inventory_entries = self._process_inventory_reduction(invoice_data['inventory_items'])
                integrated_transaction.journal_entries.extend(inventory_entries)
                integrated_transaction.inventory_data = invoice_data['inventory_items']
            
            # Step 3: Process GST calculations
            if invoice_data.get('gst_details'):
                gst_entries = self._process_gst_for_sales(invoice_data['gst_details'])
                integrated_transaction.journal_entries.extend(gst_entries)
                integrated_transaction.gst_data = invoice_data['gst_details']
            
            # Step 4: Calculate totals
            integrated_transaction.amount_total = Decimal(str(invoice_data.get('total_amount', 0)))
            integrated_transaction.tax_amount = Decimal(str(invoice_data.get('tax_amount', 0)))
            
            # Step 5: Post to accounting engine
            posting_result = self._post_to_accounting_engine(integrated_transaction)
            
            # Step 6: Update inventory records
            if invoice_data.get('inventory_items'):
                inventory_update_result = self._update_inventory_records(invoice_data['inventory_items'], 'reduction')
            
            # Step 7: Create GST record
            if invoice_data.get('gst_details'):
                gst_record_result = self._create_gst_record(invoice_data, 'sales')
            
            integrated_transaction.status = "completed"
            self.integrated_transactions[transaction_id] = integrated_transaction
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'integration_type': IntegrationType.INVOICE_TO_JOURNAL.value,
                'journal_entries_created': len(integrated_transaction.journal_entries),
                'accounting_engine_updated': posting_result.get('success', False),
                'inventory_updated': bool(invoice_data.get('inventory_items')),
                'gst_record_created': bool(invoice_data.get('gst_details')),
                'amount_total': float(integrated_transaction.amount_total),
                'tax_amount': float(integrated_transaction.tax_amount),
                'integration_summary': self._generate_integration_summary(integrated_transaction)
            }
            
        except Exception as e:
            logger.error(f"Error in sales invoice integration: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'integration_type': IntegrationType.INVOICE_TO_JOURNAL.value
            }
    
    def process_purchase_invoice_integration(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process purchase invoice with automatic inventory addition and GST credit
        """
        try:
            logger.info(f"Processing purchase invoice integration: {invoice_data.get('invoice_number')}")
            
            transaction_id = str(uuid.uuid4())
            
            # Create integrated transaction
            integrated_transaction = IntegratedTransaction(
                transaction_id=transaction_id,
                transaction_type=TransactionCategory.PURCHASE_INVOICE,
                invoice_data=invoice_data
            )
            
            # Step 1: Process purchase invoice journal entries
            purchase_entries = self._create_purchase_journal_entries(invoice_data)
            integrated_transaction.journal_entries.extend(purchase_entries)
            
            # Step 2: Process inventory addition (if applicable)
            if invoice_data.get('inventory_items'):
                inventory_entries = self._process_inventory_addition(invoice_data['inventory_items'])
                integrated_transaction.journal_entries.extend(inventory_entries)
                integrated_transaction.inventory_data = invoice_data['inventory_items']
            
            # Step 3: Process GST input credit
            if invoice_data.get('gst_details'):
                gst_entries = self._process_gst_for_purchase(invoice_data['gst_details'])
                integrated_transaction.journal_entries.extend(gst_entries)
                integrated_transaction.gst_data = invoice_data['gst_details']
            
            # Step 4: Calculate totals
            integrated_transaction.amount_total = Decimal(str(invoice_data.get('total_amount', 0)))
            integrated_transaction.tax_amount = Decimal(str(invoice_data.get('tax_amount', 0)))
            
            # Step 5: Post to accounting engine
            posting_result = self._post_to_accounting_engine(integrated_transaction)
            
            # Step 6: Update inventory records
            if invoice_data.get('inventory_items'):
                inventory_update_result = self._update_inventory_records(invoice_data['inventory_items'], 'addition')
            
            # Step 7: Create GST record
            if invoice_data.get('gst_details'):
                gst_record_result = self._create_gst_record(invoice_data, 'purchase')
            
            integrated_transaction.status = "completed"
            self.integrated_transactions[transaction_id] = integrated_transaction
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'integration_type': IntegrationType.INVOICE_TO_JOURNAL.value,
                'journal_entries_created': len(integrated_transaction.journal_entries),
                'accounting_engine_updated': posting_result.get('success', False),
                'inventory_updated': bool(invoice_data.get('inventory_items')),
                'gst_record_created': bool(invoice_data.get('gst_details')),
                'amount_total': float(integrated_transaction.amount_total),
                'tax_amount': float(integrated_transaction.tax_amount),
                'integration_summary': self._generate_integration_summary(integrated_transaction)
            }
            
        except Exception as e:
            logger.error(f"Error in purchase invoice integration: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'integration_type': IntegrationType.INVOICE_TO_JOURNAL.value
            }
    
    def _create_sales_journal_entries(self, invoice_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create journal entries for sales invoice"""
        entries = []
        amount = Decimal(str(invoice_data.get('amount', 0)))
        tax_amount = Decimal(str(invoice_data.get('tax_amount', 0)))
        
        # Debit: Accounts Receivable
        entries.append({
            'account_code': self.account_mappings['accounts_receivable'],
            'account_name': 'Accounts Receivable',
            'debit_amount': float(amount + tax_amount),
            'credit_amount': 0,
            'description': f"Sales Invoice: {invoice_data.get('invoice_number')} - {invoice_data.get('party_name')}",
            'reference': invoice_data.get('invoice_number'),
            'transaction_date': invoice_data.get('invoice_date', datetime.now())
        })
        
        # Credit: Sales Revenue
        entries.append({
            'account_code': self.account_mappings['sales_revenue'],
            'account_name': 'Sales Revenue',
            'debit_amount': 0,
            'credit_amount': float(amount),
            'description': f"Sales Revenue - {invoice_data.get('description', '')}",
            'reference': invoice_data.get('invoice_number'),
            'transaction_date': invoice_data.get('invoice_date', datetime.now())
        })
        
        # Credit: Sales Tax Payable (if tax applicable)
        if tax_amount > 0:
            entries.append({
                'account_code': self.account_mappings['sales_tax_payable'],
                'account_name': 'Sales Tax Payable',
                'debit_amount': 0,
                'credit_amount': float(tax_amount),
                'description': f"Sales Tax - {invoice_data.get('invoice_number')}",
                'reference': invoice_data.get('invoice_number'),
                'transaction_date': invoice_data.get('invoice_date', datetime.now())
            })
        
        return entries
    
    def _create_purchase_journal_entries(self, invoice_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create journal entries for purchase invoice"""
        entries = []
        amount = Decimal(str(invoice_data.get('amount', 0)))
        tax_amount = Decimal(str(invoice_data.get('tax_amount', 0)))
        
        # Debit: Purchase Expense (or Inventory if inventory item)
        account_code = self.account_mappings['inventory_account'] if invoice_data.get('is_inventory_item') else self.account_mappings['purchase_expense']
        account_name = 'Inventory' if invoice_data.get('is_inventory_item') else 'Purchase Expense'
        
        entries.append({
            'account_code': account_code,
            'account_name': account_name,
            'debit_amount': float(amount),
            'credit_amount': 0,
            'description': f"Purchase Invoice: {invoice_data.get('invoice_number')} - {invoice_data.get('party_name')}",
            'reference': invoice_data.get('invoice_number'),
            'transaction_date': invoice_data.get('invoice_date', datetime.now())
        })
        
        # Debit: Purchase Tax Receivable (if tax applicable)
        if tax_amount > 0:
            entries.append({
                'account_code': self.account_mappings['purchase_tax_receivable'],
                'account_name': 'Purchase Tax Receivable',
                'debit_amount': float(tax_amount),
                'credit_amount': 0,
                'description': f"Purchase Tax - {invoice_data.get('invoice_number')}",
                'reference': invoice_data.get('invoice_number'),
                'transaction_date': invoice_data.get('invoice_date', datetime.now())
            })
        
        # Credit: Accounts Payable
        entries.append({
            'account_code': self.account_mappings['accounts_payable'],
            'account_name': 'Accounts Payable',
            'debit_amount': 0,
            'credit_amount': float(amount + tax_amount),
            'description': f"Purchase from {invoice_data.get('party_name')}",
            'reference': invoice_data.get('invoice_number'),
            'transaction_date': invoice_data.get('invoice_date', datetime.now())
        })
        
        return entries
    
    def _process_inventory_reduction(self, inventory_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process inventory reduction for sales"""
        entries = []
        
        for item in inventory_items:
            quantity = Decimal(str(item.get('quantity', 0)))
            unit_cost = Decimal(str(item.get('unit_cost', 0)))
            total_cost = quantity * unit_cost
            
            # Debit: Cost of Goods Sold
            entries.append({
                'account_code': self.account_mappings['cost_of_goods_sold'],
                'account_name': 'Cost of Goods Sold',
                'debit_amount': float(total_cost),
                'credit_amount': 0,
                'description': f"COGS - {item.get('item_name')} (Qty: {quantity})",
                'reference': item.get('reference', ''),
                'transaction_date': datetime.now()
            })
            
            # Credit: Inventory
            entries.append({
                'account_code': self.account_mappings['inventory_account'],
                'account_name': 'Inventory',
                'debit_amount': 0,
                'credit_amount': float(total_cost),
                'description': f"Inventory Reduction - {item.get('item_name')}",
                'reference': item.get('reference', ''),
                'transaction_date': datetime.now()
            })
        
        return entries
    
    def _process_inventory_addition(self, inventory_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process inventory addition for purchases"""
        entries = []
        
        for item in inventory_items:
            quantity = Decimal(str(item.get('quantity', 0)))
            unit_cost = Decimal(str(item.get('unit_cost', 0)))
            total_cost = quantity * unit_cost
            
            # Debit: Inventory
            entries.append({
                'account_code': self.account_mappings['inventory_account'],
                'account_name': 'Inventory',
                'debit_amount': float(total_cost),
                'credit_amount': 0,
                'description': f"Inventory Addition - {item.get('item_name')} (Qty: {quantity})",
                'reference': item.get('reference', ''),
                'transaction_date': datetime.now()
            })
        
        return entries
    
    def _process_gst_for_sales(self, gst_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process GST entries for sales (output GST)"""
        entries = []
        
        for gst_type, amount in gst_details.items():
            if amount > 0 and gst_type in self.gst_account_mappings:
                entries.append({
                    'account_code': self.gst_account_mappings[gst_type]['output'],
                    'account_name': f'{gst_type} Output Liability',
                    'debit_amount': 0,
                    'credit_amount': float(amount),
                    'description': f'{gst_type} Output Tax',
                    'reference': gst_details.get('gst_number', ''),
                    'transaction_date': datetime.now()
                })
        
        return entries
    
    def _process_gst_for_purchase(self, gst_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process GST entries for purchase (input GST credit)"""
        entries = []
        
        for gst_type, amount in gst_details.items():
            if amount > 0 and gst_type in self.gst_account_mappings:
                entries.append({
                    'account_code': self.gst_account_mappings[gst_type]['input'],
                    'account_name': f'{gst_type} Input Credit',
                    'debit_amount': float(amount),
                    'credit_amount': 0,
                    'description': f'{gst_type} Input Tax Credit',
                    'reference': gst_details.get('gst_number', ''),
                    'transaction_date': datetime.now()
                })
        
        return entries
    
    def _post_to_accounting_engine(self, integrated_transaction: IntegratedTransaction) -> Dict[str, Any]:
        """Post integrated transaction to accounting engine"""
        try:
            # Convert journal entries to format expected by accounting engine
            processed_entries = []
            for entry in integrated_transaction.journal_entries:
                processed_entry = {
                    'account_code': entry['account_code'],
                    'account_name': entry['account_name'],
                    'debit_amount': entry['debit_amount'],
                    'credit_amount': entry['credit_amount'],
                    'description': entry['description'],
                    'reference': entry.get('reference', ''),
                    'transaction_date': entry.get('transaction_date', datetime.now())
                }
                processed_entries.append(processed_entry)
            
            # Use accounting engine to process entries
            if hasattr(self.accounting_engine, 'add_journal_entries'):
                result = self.accounting_engine.add_journal_entries(processed_entries)
            else:
                # Fallback to manual entry addition
                result = self._manual_journal_entry_addition(processed_entries)
            
            return {
                'success': True,
                'entries_added': len(processed_entries),
                'accounting_result': result
            }
            
        except Exception as e:
            logger.error(f"Error posting to accounting engine: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _manual_journal_entry_addition(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Manual addition of journal entries to database"""
        try:
            added_entries = []
            
            for entry in entries:
                journal_entry = JournalEntry(
                    company_id=self.company_id,
                    account_code=entry['account_code'],
                    account_name=entry['account_name'],
                    debit_amount=entry['debit_amount'],
                    credit_amount=entry['credit_amount'],
                    description=entry['description'],
                    reference_number=entry.get('reference', ''),
                    transaction_date=entry.get('transaction_date', datetime.now()),
                    created_by=self.user_id,
                    entry_date=datetime.now()
                )
                
                db.session.add(journal_entry)
                added_entries.append(journal_entry)
            
            db.session.commit()
            
            return {
                'success': True,
                'entries_added': len(added_entries),
                'message': 'Journal entries added successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in manual journal entry addition: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_inventory_records(self, inventory_items: List[Dict[str, Any]], operation: str) -> Dict[str, Any]:
        """Update inventory records in database"""
        try:
            updated_items = []
            
            for item_data in inventory_items:
                item_code = item_data.get('item_code')
                quantity = Decimal(str(item_data.get('quantity', 0)))
                
                # Find existing inventory item
                inventory_item = InventoryItem.query.filter_by(
                    item_code=item_code,
                    company_id=self.company_id
                ).first()
                
                if inventory_item:
                    if operation == 'addition':
                        inventory_item.current_stock += float(quantity)
                    elif operation == 'reduction':
                        inventory_item.current_stock -= float(quantity)
                        # Ensure stock doesn't go negative
                        if inventory_item.current_stock < 0:
                            inventory_item.current_stock = 0
                    
                    inventory_item.last_updated = datetime.now()
                    updated_items.append(inventory_item)
                else:
                    # Create new inventory item if it doesn't exist (for additions)
                    if operation == 'addition':
                        new_item = InventoryItem(
                            company_id=self.company_id,
                            item_code=item_code,
                            item_name=item_data.get('item_name', ''),
                            current_stock=float(quantity),
                            unit_cost=float(item_data.get('unit_cost', 0)),
                            reorder_level=float(item_data.get('reorder_level', 10)),
                            is_active=True,
                            created_at=datetime.now(),
                            last_updated=datetime.now()
                        )
                        db.session.add(new_item)
                        updated_items.append(new_item)
            
            db.session.commit()
            
            return {
                'success': True,
                'items_updated': len(updated_items),
                'operation': operation
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating inventory records: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_gst_record(self, invoice_data: Dict[str, Any], transaction_type: str) -> Dict[str, Any]:
        """Create GST record for compliance"""
        try:
            gst_record = GSTRecord(
                company_id=self.company_id,
                invoice_number=invoice_data.get('invoice_number'),
                party_name=invoice_data.get('party_name'),
                invoice_date=invoice_data.get('invoice_date', datetime.now()),
                invoice_amount=float(invoice_data.get('amount', 0)),
                tax_amount=float(invoice_data.get('tax_amount', 0)),
                total_tax=float(invoice_data.get('tax_amount', 0)),
                transaction_type=transaction_type,
                gst_number=invoice_data.get('gst_number', ''),
                return_period=datetime.now().strftime('%m-%Y'),
                filed_date=None,
                status='pending',
                created_at=datetime.now()
            )
            
            db.session.add(gst_record)
            db.session.commit()
            
            return {
                'success': True,
                'gst_record_id': gst_record.id,
                'message': 'GST record created successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating GST record: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_integration_summary(self, transaction: IntegratedTransaction) -> Dict[str, Any]:
        """Generate comprehensive integration summary"""
        return {
            'transaction_id': transaction.transaction_id,
            'transaction_type': transaction.transaction_type.value,
            'integration_timestamp': transaction.integration_timestamp.isoformat(),
            'total_journal_entries': len(transaction.journal_entries),
            'amount_total': float(transaction.amount_total),
            'tax_amount': float(transaction.tax_amount),
            'has_inventory_impact': bool(transaction.inventory_data),
            'has_gst_impact': bool(transaction.gst_data),
            'status': transaction.status,
            'affected_accounts': list(set([entry['account_code'] for entry in transaction.journal_entries])),
            'integration_workflow': self._describe_workflow(transaction.transaction_type)
        }
    
    def _describe_workflow(self, transaction_type: TransactionCategory) -> List[str]:
        """Describe the integration workflow steps"""
        workflows = {
            TransactionCategory.SALES_INVOICE: [
                "1. Create sales journal entries (A/R Dr, Sales Cr)",
                "2. Process inventory reduction (COGS Dr, Inventory Cr)",
                "3. Calculate and record GST output liability",
                "4. Update inventory records",
                "5. Create GST compliance record",
                "6. Post to accounting engine",
                "7. Generate updated financial reports"
            ],
            TransactionCategory.PURCHASE_INVOICE: [
                "1. Create purchase journal entries (Expense/Inventory Dr, A/P Cr)",
                "2. Process inventory addition",
                "3. Calculate and record GST input credit",
                "4. Update inventory records",
                "5. Create GST compliance record",
                "6. Post to accounting engine",
                "7. Generate updated financial reports"
            ]
        }
        
        return workflows.get(transaction_type, ["Standard integration workflow"])
    
    def generate_comprehensive_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive report of all integrations"""
        try:
            # Get all integrated transactions
            transactions = list(self.integrated_transactions.values())
            
            # Calculate statistics
            total_transactions = len(transactions)
            completed_transactions = len([t for t in transactions if t.status == 'completed'])
            total_amount = sum([t.amount_total for t in transactions])
            total_tax = sum([t.tax_amount for t in transactions])
            
            # Group by transaction type
            type_breakdown = {}
            for transaction in transactions:
                tx_type = transaction.transaction_type.value
                if tx_type not in type_breakdown:
                    type_breakdown[tx_type] = {
                        'count': 0,
                        'total_amount': Decimal('0'),
                        'total_tax': Decimal('0')
                    }
                type_breakdown[tx_type]['count'] += 1
                type_breakdown[tx_type]['total_amount'] += transaction.amount_total
                type_breakdown[tx_type]['total_tax'] += transaction.tax_amount
            
            # Recent transactions (last 10)
            recent_transactions = sorted(transactions, key=lambda x: x.integration_timestamp, reverse=True)[:10]
            
            return {
                'success': True,
                'report_generated_at': datetime.now().isoformat(),
                'summary': {
                    'total_transactions': total_transactions,
                    'completed_transactions': completed_transactions,
                    'success_rate': (completed_transactions / total_transactions * 100) if total_transactions > 0 else 0,
                    'total_amount': float(total_amount),
                    'total_tax': float(total_tax)
                },
                'transaction_type_breakdown': {
                    tx_type: {
                        'count': data['count'],
                        'total_amount': float(data['total_amount']),
                        'total_tax': float(data['total_tax'])
                    }
                    for tx_type, data in type_breakdown.items()
                },
                'recent_transactions': [
                    self._generate_integration_summary(tx) for tx in recent_transactions
                ],
                'integration_health': {
                    'active_integrations': total_transactions,
                    'system_status': 'healthy' if completed_transactions == total_transactions else 'warning',
                    'last_integration': recent_transactions[0].integration_timestamp.isoformat() if recent_transactions else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating integration report: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_template_for_ar_ap_br_mapping(self, file_path: str, template_type: str) -> Dict[str, Any]:
        """
        Analyze uploaded template and automatically categorize for AR/AP/BR mapping
        """
        try:
            logger.info(f"Analyzing template: {file_path} for AR/AP/BR mapping")
            
            # Read the uploaded file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, sheet_name=0)
            
            # Column mapping for different transaction types
            column_indicators = {
                'sales_indicators': ['customer', 'sales', 'revenue', 'invoice_to', 'bill_to', 'receivable'],
                'purchase_indicators': ['vendor', 'supplier', 'purchase', 'expense', 'bill_from', 'payable'],
                'bank_indicators': ['bank', 'transaction', 'balance', 'deposit', 'withdrawal', 'statement'],
                'inventory_indicators': ['item', 'product', 'quantity', 'stock', 'inventory', 'sku'],
                'gst_indicators': ['gst', 'tax', 'cgst', 'sgst', 'igst', 'vat']
            }
            
            # Analyze columns to determine transaction types
            columns_lower = [col.lower().strip() for col in df.columns]
            analysis_result = {
                'file_path': file_path,
                'template_type': template_type,
                'total_rows': len(df),
                'columns_found': list(df.columns),
                'has_sales_transactions': False,
                'has_purchase_transactions': False,
                'has_bank_transactions': False,
                'has_inventory_data': False,
                'has_gst_data': False,
                'sales_data': [],
                'purchase_data': [],
                'bank_data': [],
                'inventory_data': [],
                'gst_data': []
            }
            
            # Check for different transaction types
            for col in columns_lower:
                if any(indicator in col for indicator in column_indicators['sales_indicators']):
                    analysis_result['has_sales_transactions'] = True
                if any(indicator in col for indicator in column_indicators['purchase_indicators']):
                    analysis_result['has_purchase_transactions'] = True
                if any(indicator in col for indicator in column_indicators['bank_indicators']):
                    analysis_result['has_bank_transactions'] = True
                if any(indicator in col for indicator in column_indicators['inventory_indicators']):
                    analysis_result['has_inventory_data'] = True
                if any(indicator in col for indicator in column_indicators['gst_indicators']):
                    analysis_result['has_gst_data'] = True
            
            # Process data based on identified types
            if analysis_result['has_sales_transactions']:
                analysis_result['sales_data'] = self._extract_sales_data(df)
            
            if analysis_result['has_purchase_transactions']:
                analysis_result['purchase_data'] = self._extract_purchase_data(df)
            
            if analysis_result['has_bank_transactions']:
                analysis_result['bank_data'] = self._extract_bank_data(df)
            
            if analysis_result['has_inventory_data']:
                analysis_result['inventory_data'] = self._extract_inventory_data(df)
            
            if analysis_result['has_gst_data']:
                analysis_result['gst_data'] = self._extract_gst_data(df)
            
            logger.info(f"Template analysis completed: AR={analysis_result['has_sales_transactions']}, "
                       f"AP={analysis_result['has_purchase_transactions']}, "
                       f"BR={analysis_result['has_bank_transactions']}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing template: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _extract_sales_data(self, df) -> List[Dict[str, Any]]:
        """Extract sales transaction data from DataFrame"""
        sales_data = []
        try:
            for _, row in df.iterrows():
                # Look for common sales indicators
                sales_item = {
                    'invoice_number': self._safe_get_value(row, ['invoice_number', 'invoice_no', 'bill_no']),
                    'party_name': self._safe_get_value(row, ['customer_name', 'party_name', 'customer']),
                    'amount': self._safe_get_numeric_value(row, ['amount', 'total_amount', 'net_amount']),
                    'tax_amount': self._safe_get_numeric_value(row, ['tax_amount', 'gst_amount', 'tax']),
                    'invoice_date': self._safe_get_date_value(row, ['invoice_date', 'date', 'bill_date']),
                    'description': self._safe_get_value(row, ['description', 'item_description', 'particulars']),
                    'is_inventory_item': self._check_inventory_indicators(row),
                    'inventory_items': self._extract_inventory_items(row) if self._check_inventory_indicators(row) else [],
                    'gst_details': self._extract_gst_details(row)
                }
                
                if sales_item['invoice_number'] and sales_item['party_name']:
                    sales_data.append(sales_item)
        except Exception as e:
            logger.error(f"Error extracting sales data: {str(e)}")
        
        return sales_data
    
    def _extract_purchase_data(self, df) -> List[Dict[str, Any]]:
        """Extract purchase transaction data from DataFrame"""
        purchase_data = []
        try:
            for _, row in df.iterrows():
                purchase_item = {
                    'invoice_number': self._safe_get_value(row, ['invoice_number', 'bill_no', 'po_number']),
                    'party_name': self._safe_get_value(row, ['vendor_name', 'supplier_name', 'party_name']),
                    'amount': self._safe_get_numeric_value(row, ['amount', 'total_amount', 'net_amount']),
                    'tax_amount': self._safe_get_numeric_value(row, ['tax_amount', 'gst_amount', 'tax']),
                    'invoice_date': self._safe_get_date_value(row, ['invoice_date', 'date', 'bill_date']),
                    'description': self._safe_get_value(row, ['description', 'item_description', 'particulars']),
                    'is_inventory_item': self._check_inventory_indicators(row),
                    'inventory_items': self._extract_inventory_items(row) if self._check_inventory_indicators(row) else [],
                    'gst_details': self._extract_gst_details(row)
                }
                
                if purchase_item['invoice_number'] and purchase_item['party_name']:
                    purchase_data.append(purchase_item)
        except Exception as e:
            logger.error(f"Error extracting purchase data: {str(e)}")
        
        return purchase_data
    
    def _extract_bank_data(self, df) -> List[Dict[str, Any]]:
        """Extract bank transaction data from DataFrame"""
        bank_data = []
        try:
            for _, row in df.iterrows():
                bank_item = {
                    'transaction_date': self._safe_get_date_value(row, ['date', 'transaction_date', 'value_date']),
                    'description': self._safe_get_value(row, ['description', 'particulars', 'narration']),
                    'debit_amount': self._safe_get_numeric_value(row, ['debit', 'debit_amount', 'withdrawal']),
                    'credit_amount': self._safe_get_numeric_value(row, ['credit', 'credit_amount', 'deposit']),
                    'balance': self._safe_get_numeric_value(row, ['balance', 'running_balance']),
                    'reference': self._safe_get_value(row, ['reference', 'ref_no', 'cheque_no'])
                }
                
                if bank_item['transaction_date'] and (bank_item['debit_amount'] > 0 or bank_item['credit_amount'] > 0):
                    bank_data.append(bank_item)
        except Exception as e:
            logger.error(f"Error extracting bank data: {str(e)}")
        
        return bank_data
    
    def _extract_inventory_data(self, df) -> List[Dict[str, Any]]:
        """Extract inventory data from DataFrame"""
        inventory_data = []
        try:
            for _, row in df.iterrows():
                inventory_item = {
                    'item_code': self._safe_get_value(row, ['item_code', 'sku', 'product_code']),
                    'item_name': self._safe_get_value(row, ['item_name', 'product_name', 'description']),
                    'quantity': self._safe_get_numeric_value(row, ['quantity', 'qty', 'units']),
                    'unit_cost': self._safe_get_numeric_value(row, ['unit_cost', 'rate', 'price']),
                    'total_value': self._safe_get_numeric_value(row, ['total_value', 'amount'])
                }
                
                if inventory_item['item_code'] and inventory_item['quantity'] > 0:
                    inventory_data.append(inventory_item)
        except Exception as e:
            logger.error(f"Error extracting inventory data: {str(e)}")
        
        return inventory_data
    
    def _extract_gst_data(self, df) -> List[Dict[str, Any]]:
        """Extract GST data from DataFrame"""
        gst_data = []
        try:
            for _, row in df.iterrows():
                gst_item = {
                    'CGST': self._safe_get_numeric_value(row, ['cgst', 'cgst_amount']),
                    'SGST': self._safe_get_numeric_value(row, ['sgst', 'sgst_amount']),
                    'IGST': self._safe_get_numeric_value(row, ['igst', 'igst_amount']),
                    'gst_number': self._safe_get_value(row, ['gst_number', 'gstin', 'gst_id'])
                }
                
                if any(gst_item[key] > 0 for key in ['CGST', 'SGST', 'IGST']):
                    gst_data.append(gst_item)
        except Exception as e:
            logger.error(f"Error extracting GST data: {str(e)}")
        
        return gst_data
    
    def _safe_get_value(self, row, column_names: List[str]) -> str:
        """Safely get string value from row using multiple possible column names"""
        for col_name in column_names:
            for actual_col in row.index:
                if col_name.lower() in actual_col.lower():
                    value = row[actual_col]
                    return str(value).strip() if pd.notna(value) else ""
        return ""
    
    def _safe_get_numeric_value(self, row, column_names: List[str]) -> float:
        """Safely get numeric value from row using multiple possible column names"""
        for col_name in column_names:
            for actual_col in row.index:
                if col_name.lower() in actual_col.lower():
                    value = row[actual_col]
                    if pd.notna(value):
                        try:
                            return float(str(value).replace(',', '').replace('₹', '').strip())
                        except (ValueError, TypeError):
                            continue
        return 0.0
    
    def _safe_get_date_value(self, row, column_names: List[str]):
        """Safely get date value from row using multiple possible column names"""
        for col_name in column_names:
            for actual_col in row.index:
                if col_name.lower() in actual_col.lower():
                    value = row[actual_col]
                    if pd.notna(value):
                        if isinstance(value, datetime):
                            return value
                        try:
                            return pd.to_datetime(value)
                        except:
                            continue
        return datetime.now()
    
    def _check_inventory_indicators(self, row) -> bool:
        """Check if row contains inventory-related data"""
        inventory_indicators = ['quantity', 'qty', 'units', 'item_code', 'sku', 'product']
        for col in row.index:
            if any(indicator in col.lower() for indicator in inventory_indicators):
                if pd.notna(row[col]) and str(row[col]).strip():
                    return True
        return False
    
    def _extract_inventory_items(self, row) -> List[Dict[str, Any]]:
        """Extract inventory items from a single row"""
        items = []
        if self._check_inventory_indicators(row):
            item = {
                'item_code': self._safe_get_value(row, ['item_code', 'sku', 'product_code']),
                'item_name': self._safe_get_value(row, ['item_name', 'product_name', 'description']),
                'quantity': self._safe_get_numeric_value(row, ['quantity', 'qty', 'units']),
                'unit_cost': self._safe_get_numeric_value(row, ['unit_cost', 'rate', 'price']),
                'reference': self._safe_get_value(row, ['reference', 'invoice_number'])
            }
            if item['item_code'] or item['item_name']:
                items.append(item)
        return items
    
    def _extract_gst_details(self, row) -> Dict[str, float]:
        """Extract GST details from a single row"""
        return {
            'CGST': self._safe_get_numeric_value(row, ['cgst', 'cgst_amount']),
            'SGST': self._safe_get_numeric_value(row, ['sgst', 'sgst_amount']),
            'IGST': self._safe_get_numeric_value(row, ['igst', 'igst_amount']),
            'gst_number': self._safe_get_value(row, ['gst_number', 'gstin', 'gst_id'])
        }
    
    def process_bank_reconciliation_integration(self, bank_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process bank reconciliation data and integrate with journal entries"""
        try:
            logger.info(f"Processing bank reconciliation integration for {len(bank_data)} transactions")
            
            transaction_id = str(uuid.uuid4())
            
            integrated_transaction = IntegratedTransaction(
                transaction_id=transaction_id,
                transaction_type=TransactionCategory.SALES_INVOICE,  # Will be determined by bank data
                invoice_data={'bank_transactions': bank_data}
            )
            
            # Process bank transactions and create journal entries
            for bank_tx in bank_data:
                if bank_tx.get('debit_amount', 0) > 0:
                    # Bank debit (money going out)
                    entry = {
                        'account_code': '5000',  # Expense account
                        'account_name': 'Bank Charges/Expenses',
                        'debit_amount': bank_tx['debit_amount'],
                        'credit_amount': 0,
                        'description': f"Bank Debit: {bank_tx.get('description', '')}",
                        'reference': bank_tx.get('reference', ''),
                        'transaction_date': bank_tx.get('transaction_date', datetime.now())
                    }
                    integrated_transaction.journal_entries.append(entry)
                    
                    # Corresponding credit to bank
                    entry_credit = {
                        'account_code': '1000',  # Bank account
                        'account_name': 'Bank Account',
                        'debit_amount': 0,
                        'credit_amount': bank_tx['debit_amount'],
                        'description': f"Bank Debit: {bank_tx.get('description', '')}",
                        'reference': bank_tx.get('reference', ''),
                        'transaction_date': bank_tx.get('transaction_date', datetime.now())
                    }
                    integrated_transaction.journal_entries.append(entry_credit)
                
                elif bank_tx.get('credit_amount', 0) > 0:
                    # Bank credit (money coming in)
                    entry = {
                        'account_code': '1000',  # Bank account
                        'account_name': 'Bank Account',
                        'debit_amount': bank_tx['credit_amount'],
                        'credit_amount': 0,
                        'description': f"Bank Credit: {bank_tx.get('description', '')}",
                        'reference': bank_tx.get('reference', ''),
                        'transaction_date': bank_tx.get('transaction_date', datetime.now())
                    }
                    integrated_transaction.journal_entries.append(entry)
                    
                    # Corresponding credit (could be revenue or receivable payment)
                    entry_credit = {
                        'account_code': '4000',  # Revenue account (default)
                        'account_name': 'Revenue/Income',
                        'debit_amount': 0,
                        'credit_amount': bank_tx['credit_amount'],
                        'description': f"Bank Credit: {bank_tx.get('description', '')}",
                        'reference': bank_tx.get('reference', ''),
                        'transaction_date': bank_tx.get('transaction_date', datetime.now())
                    }
                    integrated_transaction.journal_entries.append(entry_credit)
            
            # Post to accounting engine
            posting_result = self._post_to_accounting_engine(integrated_transaction)
            
            integrated_transaction.status = "completed"
            self.integrated_transactions[transaction_id] = integrated_transaction
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'integration_type': 'bank_reconciliation',
                'journal_entries_created': len(integrated_transaction.journal_entries),
                'bank_transactions_processed': len(bank_data),
                'accounting_engine_updated': posting_result.get('success', False)
            }
            
        except Exception as e:
            logger.error(f"Error in bank reconciliation integration: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'integration_type': 'bank_reconciliation'
            }
    
    def generate_comprehensive_journal_reports(self) -> Dict[str, Any]:
        """Generate comprehensive journal reports from all integrated transactions"""
        try:
            logger.info("Generating comprehensive journal reports from integrated transactions")
            
            all_entries = []
            for transaction in self.integrated_transactions.values():
                all_entries.extend(transaction.journal_entries)
            
            if not all_entries:
                return {
                    'success': True,
                    'reports': [],
                    'message': 'No journal entries found to generate reports'
                }
            
            # Generate different types of reports
            reports = {
                'journal_register': self._generate_journal_register(all_entries),
                'ledger_summary': self._generate_ledger_summary(all_entries),
                'trial_balance': self._generate_trial_balance(all_entries),
                'account_wise_summary': self._generate_account_wise_summary(all_entries)
            }
            
            return {
                'success': True,
                'reports': reports,
                'total_entries': len(all_entries),
                'generation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive journal reports: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_journal_register(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate journal register report"""
        return {
            'report_type': 'Journal Register',
            'entries': entries,
            'total_debits': sum([entry.get('debit_amount', 0) for entry in entries]),
            'total_credits': sum([entry.get('credit_amount', 0) for entry in entries]),
            'entry_count': len(entries)
        }
    
    def _generate_ledger_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate ledger summary by account"""
        ledger_summary = {}
        
        for entry in entries:
            account_code = entry.get('account_code', 'Unknown')
            account_name = entry.get('account_name', 'Unknown Account')
            
            if account_code not in ledger_summary:
                ledger_summary[account_code] = {
                    'account_name': account_name,
                    'total_debits': 0,
                    'total_credits': 0,
                    'net_balance': 0,
                    'entry_count': 0
                }
            
            ledger_summary[account_code]['total_debits'] += entry.get('debit_amount', 0)
            ledger_summary[account_code]['total_credits'] += entry.get('credit_amount', 0)
            ledger_summary[account_code]['net_balance'] = (
                ledger_summary[account_code]['total_debits'] - 
                ledger_summary[account_code]['total_credits']
            )
            ledger_summary[account_code]['entry_count'] += 1
        
        return {
            'report_type': 'Ledger Summary',
            'accounts': ledger_summary,
            'total_accounts': len(ledger_summary)
        }
    
    def _generate_trial_balance(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate trial balance"""
        ledger_summary = self._generate_ledger_summary(entries)['accounts']
        
        trial_balance = []
        total_debits = 0
        total_credits = 0
        
        for account_code, account_data in ledger_summary.items():
            balance = account_data['net_balance']
            debit_balance = balance if balance > 0 else 0
            credit_balance = abs(balance) if balance < 0 else 0
            
            trial_balance.append({
                'account_code': account_code,
                'account_name': account_data['account_name'],
                'debit_balance': debit_balance,
                'credit_balance': credit_balance
            })
            
            total_debits += debit_balance
            total_credits += credit_balance
        
        return {
            'report_type': 'Trial Balance',
            'accounts': trial_balance,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'is_balanced': abs(total_debits - total_credits) < 0.01
        }
    
    def _generate_account_wise_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate account-wise transaction summary"""
        account_summary = {}
        
        for entry in entries:
            account_code = entry.get('account_code', 'Unknown')
            
            if account_code not in account_summary:
                account_summary[account_code] = {
                    'account_name': entry.get('account_name', 'Unknown Account'),
                    'transactions': [],
                    'total_amount': 0
                }
            
            account_summary[account_code]['transactions'].append({
                'date': entry.get('transaction_date', datetime.now()).isoformat() if isinstance(entry.get('transaction_date'), datetime) else str(entry.get('transaction_date', '')),
                'description': entry.get('description', ''),
                'debit_amount': entry.get('debit_amount', 0),
                'credit_amount': entry.get('credit_amount', 0),
                'reference': entry.get('reference', '')
            })
            
            account_summary[account_code]['total_amount'] += (
                entry.get('debit_amount', 0) + entry.get('credit_amount', 0)
            )
        
        return {
            'report_type': 'Account-wise Summary',
            'accounts': account_summary,
            'total_accounts': len(account_summary)
        }
    
    def create_integrated_reports_package(self) -> Dict[str, Any]:
        """Create downloadable reports package"""
        try:
            # Generate reports
            reports = self.generate_comprehensive_journal_reports()
            
            if not reports.get('success'):
                return reports
            
            # Create reports package info
            package_info = {
                'package_name': f"Integrated_Accounting_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'reports_included': list(reports['reports'].keys()),
                'total_entries': reports.get('total_entries', 0),
                'generation_date': datetime.now().isoformat(),
                'download_formats': ['excel', 'pdf', 'json'],
                'package_ready': True
            }
            
            return {
                'success': True,
                'package_info': package_info,
                'reports_data': reports['reports']
            }
            
        except Exception as e:
            logger.error(f"Error creating reports package: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_integration_status_dashboard(self) -> Dict[str, Any]:
        """Get real-time integration status for dashboard"""
        try:
            # Get recent AR/AP invoices
            recent_invoices = self.ar_ap_service.get_recent_invoices(limit=20)
            
            # Get inventory status
            inventory_items = InventoryItem.query.filter_by(
                company_id=self.company_id,
                is_active=True
            ).all()
            
            # Get GST records
            gst_records = GSTRecord.query.filter_by(
                company_id=self.company_id
            ).order_by(GSTRecord.created_at.desc()).limit(10).all()
            
            # Calculate integration metrics
            pending_integrations = len([inv for inv in recent_invoices if inv.get('integration_status') != 'completed'])
            low_stock_items = len([item for item in inventory_items if item.current_stock <= item.reorder_level])
            pending_gst_filings = len([record for record in gst_records if record.status == 'pending'])
            
            return {
                'success': True,
                'dashboard_data': {
                    'integration_metrics': {
                        'total_invoices': len(recent_invoices),
                        'pending_integrations': pending_integrations,
                        'integration_rate': ((len(recent_invoices) - pending_integrations) / len(recent_invoices) * 100) if recent_invoices else 100
                    },
                    'inventory_metrics': {
                        'total_items': len(inventory_items),
                        'low_stock_items': low_stock_items,
                        'total_inventory_value': sum([item.current_stock * item.unit_cost for item in inventory_items])
                    },
                    'gst_metrics': {
                        'total_records': len(gst_records),
                        'pending_filings': pending_gst_filings,
                        'compliance_rate': ((len(gst_records) - pending_gst_filings) / len(gst_records) * 100) if gst_records else 100
                    },
                    'system_health': {
                        'integration_engine': 'healthy',
                        'last_update': datetime.now().isoformat(),
                        'automation_level': 'high'
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting integration status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Integration Service Instance
def get_integration_service(company_id: int = 1, user_id: int = 1) -> InvoiceInventoryGSTIntegration:
    """Get integration service instance"""
    return InvoiceInventoryGSTIntegration(company_id, user_id)