"""
Automated Accounting Engine - F-AI Accountant
Comprehensive automated accounting processing with template validation and report generation
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

from app import db
from models import *
from services.validation_engine import ValidationEngine
from services.report_generator import ReportGenerator
from services.mis_report_service import MISReportService
from utils.template_generator import TemplateGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionType(Enum):
    PURCHASE = "purchase"
    SALES = "sales"
    INCOME = "income"
    EXPENSE = "expense"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    PAYMENT = "payment"
    RECEIPT = "receipt"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"

class AccountType(Enum):
    ASSETS = "assets"
    LIABILITIES = "liabilities"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSES = "expenses"

@dataclass
class AccountingEntry:
    """Represents a single accounting entry"""
    account_code: str
    account_name: str
    debit_amount: Decimal
    credit_amount: Decimal
    description: str
    reference: str
    transaction_date: datetime
    transaction_type: TransactionType

@dataclass
class ProcessingResult:
    """Results of automated accounting processing"""
    success: bool
    total_entries: int
    journal_entries: List[AccountingEntry]
    validation_errors: List[str]
    processing_log: List[str]
    generated_reports: Dict[str, str]
    balance_verification: bool

class AutomatedAccountingEngine:
    """
    Core automated accounting engine that processes templates and generates complete financial reports
    """
    
    def __init__(self, company_id: int, user_id: int):
        self.company_id = company_id
        self.user_id = user_id
        self.validation_engine = ValidationEngine()
        self.report_generator = ReportGenerator()
        self.template_generator = TemplateGenerator()
        
        # Standard Chart of Accounts
        self.standard_coa = self._initialize_standard_coa()
        
        # Transaction Classification Engine
        self.classification_engine = self._initialize_classification_engine()
        
        # Account Mapping Templates
        self.account_templates = self._initialize_account_templates()
        
    def _initialize_standard_coa(self) -> Dict[str, Dict[str, Any]]:
        """Initialize standard chart of accounts structure"""
        return {
            # Assets
            "1000": {"name": "Cash and Cash Equivalents", "type": AccountType.ASSETS, "parent": None},
            "1010": {"name": "Petty Cash", "type": AccountType.ASSETS, "parent": "1000"},
            "1020": {"name": "Bank Account - Current", "type": AccountType.ASSETS, "parent": "1000"},
            "1030": {"name": "Bank Account - Savings", "type": AccountType.ASSETS, "parent": "1000"},
            "1100": {"name": "Accounts Receivable", "type": AccountType.ASSETS, "parent": None},
            "1110": {"name": "Trade Receivables", "type": AccountType.ASSETS, "parent": "1100"},
            "1120": {"name": "Other Receivables", "type": AccountType.ASSETS, "parent": "1100"},
            "1200": {"name": "Inventory", "type": AccountType.ASSETS, "parent": None},
            "1210": {"name": "Raw Materials", "type": AccountType.ASSETS, "parent": "1200"},
            "1220": {"name": "Work in Progress", "type": AccountType.ASSETS, "parent": "1200"},
            "1230": {"name": "Finished Goods", "type": AccountType.ASSETS, "parent": "1200"},
            "1300": {"name": "Prepaid Expenses", "type": AccountType.ASSETS, "parent": None},
            "1400": {"name": "Fixed Assets", "type": AccountType.ASSETS, "parent": None},
            "1410": {"name": "Plant and Equipment", "type": AccountType.ASSETS, "parent": "1400"},
            "1420": {"name": "Accumulated Depreciation", "type": AccountType.ASSETS, "parent": "1400"},
            
            # Liabilities
            "2000": {"name": "Current Liabilities", "type": AccountType.LIABILITIES, "parent": None},
            "2010": {"name": "Accounts Payable", "type": AccountType.LIABILITIES, "parent": "2000"},
            "2020": {"name": "Accrued Expenses", "type": AccountType.LIABILITIES, "parent": "2000"},
            "2030": {"name": "Short-term Loans", "type": AccountType.LIABILITIES, "parent": "2000"},
            "2100": {"name": "Long-term Liabilities", "type": AccountType.LIABILITIES, "parent": None},
            "2110": {"name": "Long-term Loans", "type": AccountType.LIABILITIES, "parent": "2100"},
            "2200": {"name": "Tax Liabilities", "type": AccountType.LIABILITIES, "parent": None},
            "2210": {"name": "Income Tax Payable", "type": AccountType.LIABILITIES, "parent": "2200"},
            "2220": {"name": "GST Payable", "type": AccountType.LIABILITIES, "parent": "2200"},
            
            # Equity
            "3000": {"name": "Owner's Equity", "type": AccountType.EQUITY, "parent": None},
            "3010": {"name": "Share Capital", "type": AccountType.EQUITY, "parent": "3000"},
            "3020": {"name": "Retained Earnings", "type": AccountType.EQUITY, "parent": "3000"},
            "3030": {"name": "Current Year Earnings", "type": AccountType.EQUITY, "parent": "3000"},
            
            # Revenue
            "4000": {"name": "Sales Revenue", "type": AccountType.REVENUE, "parent": None},
            "4010": {"name": "Product Sales", "type": AccountType.REVENUE, "parent": "4000"},
            "4020": {"name": "Service Revenue", "type": AccountType.REVENUE, "parent": "4000"},
            "4100": {"name": "Other Income", "type": AccountType.REVENUE, "parent": None},
            "4110": {"name": "Interest Income", "type": AccountType.REVENUE, "parent": "4100"},
            "4120": {"name": "Rental Income", "type": AccountType.REVENUE, "parent": "4100"},
            
            # Expenses
            "5000": {"name": "Cost of Goods Sold", "type": AccountType.EXPENSES, "parent": None},
            "5010": {"name": "Material Costs", "type": AccountType.EXPENSES, "parent": "5000"},
            "5020": {"name": "Labor Costs", "type": AccountType.EXPENSES, "parent": "5000"},
            "5100": {"name": "Operating Expenses", "type": AccountType.EXPENSES, "parent": None},
            "5110": {"name": "Salaries and Wages", "type": AccountType.EXPENSES, "parent": "5100"},
            "5120": {"name": "Rent Expense", "type": AccountType.EXPENSES, "parent": "5100"},
            "5130": {"name": "Utilities Expense", "type": AccountType.EXPENSES, "parent": "5100"},
            "5140": {"name": "Office Supplies", "type": AccountType.EXPENSES, "parent": "5100"},
            "5150": {"name": "Marketing Expense", "type": AccountType.EXPENSES, "parent": "5100"},
            "5160": {"name": "Professional Fees", "type": AccountType.EXPENSES, "parent": "5100"},
            "5200": {"name": "Financial Expenses", "type": AccountType.EXPENSES, "parent": None},
            "5210": {"name": "Interest Expense", "type": AccountType.EXPENSES, "parent": "5200"},
            "5220": {"name": "Bank Charges", "type": AccountType.EXPENSES, "parent": "5200"},
        }
    
    def _initialize_classification_engine(self) -> Dict[str, Any]:
        """Initialize intelligent transaction classification system with standardized nomenclature"""
        return {
            # Keywords for automatic account classification
            "revenue_keywords": [
                "sales", "income", "revenue", "service", "consulting", "subscription",
                "commission", "royalty", "dividend", "interest earned", "rental income"
            ],
            "expense_keywords": {
                "5110": ["salary", "wages", "payroll", "employee", "staff", "hr", "compensation"],
                "5120": ["rent", "lease", "office rent", "warehouse rent", "facility"],
                "5130": ["utility", "electricity", "water", "gas", "internet", "phone", "telecom"],
                "5140": ["supplies", "stationery", "office supplies", "materials", "equipment"],
                "5150": ["marketing", "advertising", "promotion", "seo", "ads", "campaign"],
                "5160": ["legal", "consultant", "professional", "audit", "tax prep", "advisory"],
                "5210": ["insurance", "coverage", "premium", "policy"],
                "5000": ["cogs", "cost of goods", "inventory", "materials", "direct cost", "production"]
            },
            "asset_keywords": {
                "1020": ["bank", "checking", "savings", "deposit", "cash", "payment"],
                "1100": ["receivable", "customer", "ar", "invoice", "billing"],
                "1200": ["inventory", "stock", "goods", "materials", "products"],
                "1400": ["equipment", "machinery", "furniture", "computer", "vehicle", "asset"]
            },
            "liability_keywords": {
                "2010": ["payable", "vendor", "supplier", "ap", "bill"],
                "2030": ["loan", "borrowing", "credit", "debt", "financing"],
                "2220": ["tax", "gst", "vat", "sales tax", "duty"]
            },
            # Transaction pattern recognition
            "transaction_patterns": {
                "purchase": {
                    "indicators": ["purchase", "buy", "vendor", "supplier", "invoice"],
                    "default_accounts": {"debit": "1200", "credit": "2010"}
                },
                "sales": {
                    "indicators": ["sale", "sell", "customer", "revenue", "income"],
                    "default_accounts": {"debit": "1100", "credit": "4000"}
                },
                "expense": {
                    "indicators": ["expense", "cost", "payment", "bill", "fee"],
                    "default_accounts": {"debit": "5100", "credit": "1020"}
                },
                "transfer": {
                    "indicators": ["transfer", "move", "deposit", "withdrawal"],
                    "default_accounts": {"debit": "1020", "credit": "1030"}
                }
            }
        }
    
    def _initialize_account_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize standardized account mapping templates for smooth user experience"""
        return {
            "purchase_template": {
                "name": "Purchase Transaction Template",
                "description": "Standard template for purchasing goods/services",
                "debit_accounts": {
                    "primary": "1200",  # Inventory
                    "alternatives": ["5000", "5100"]  # COGS, Operating Expenses
                },
                "credit_accounts": {
                    "primary": "2010",  # Accounts Payable
                    "alternatives": ["1020"]  # Cash
                },
                "tax_account": "2220",  # GST Payable
                "auto_classification": True
            },
            "sales_template": {
                "name": "Sales Transaction Template",
                "description": "Standard template for sales revenue",
                "debit_accounts": {
                    "primary": "1100",  # Accounts Receivable
                    "alternatives": ["1020"]  # Cash
                },
                "credit_accounts": {
                    "primary": "4000",  # Sales Revenue
                    "alternatives": ["4010", "4020"]  # Product/Service Sales
                },
                "tax_account": "2220",  # GST Payable
                "auto_classification": True
            },
            "expense_template": {
                "name": "Expense Transaction Template",
                "description": "Standard template for operating expenses",
                "debit_accounts": {
                    "primary": "5100",  # Operating Expenses
                    "alternatives": ["5110", "5120", "5130", "5140", "5150", "5160"]
                },
                "credit_accounts": {
                    "primary": "1020",  # Cash
                    "alternatives": ["2010"]  # Accounts Payable
                },
                "tax_account": "2220",
                "auto_classification": True
            },
            "payroll_template": {
                "name": "Payroll Transaction Template",
                "description": "Standard template for employee compensation",
                "debit_accounts": {
                    "primary": "5110",  # Salaries and Wages
                    "alternatives": []
                },
                "credit_accounts": {
                    "primary": "1020",  # Cash
                    "alternatives": ["2020"]  # Accrued Expenses
                },
                "tax_account": "2210",  # Income Tax Payable
                "auto_classification": True
            },
            "asset_purchase_template": {
                "name": "Asset Purchase Template",
                "description": "Template for fixed asset acquisitions",
                "debit_accounts": {
                    "primary": "1400",  # Fixed Assets
                    "alternatives": ["1410"]  # Plant and Equipment
                },
                "credit_accounts": {
                    "primary": "1020",  # Cash
                    "alternatives": ["2010"]  # Accounts Payable
                },
                "tax_account": "2220",
                "auto_classification": True
            }
        }
    
    def classify_transaction(self, description: str, amount: float, transaction_type: str = None) -> Dict[str, str]:
        """
        Intelligently classify transaction and suggest appropriate accounts
        
        Args:
            description: Transaction description
            amount: Transaction amount
            transaction_type: Optional explicit transaction type
            
        Returns:
            Dictionary with suggested debit and credit accounts
        """
        description_lower = description.lower()
        
        # If transaction type is explicitly provided, use template
        if transaction_type and transaction_type in self.account_templates:
            template = self.account_templates[transaction_type]
            return {
                "debit_account": template["debit_accounts"]["primary"],
                "credit_account": template["credit_accounts"]["primary"],
                "tax_account": template.get("tax_account", "2220"),
                "confidence": "high",
                "template_used": transaction_type
            }
        
        # Pattern-based classification
        for pattern_name, pattern_data in self.classification_engine["transaction_patterns"].items():
            for indicator in pattern_data["indicators"]:
                if indicator in description_lower:
                    return {
                        "debit_account": pattern_data["default_accounts"]["debit"],
                        "credit_account": pattern_data["default_accounts"]["credit"],
                        "tax_account": "2220",
                        "confidence": "medium",
                        "pattern_matched": pattern_name
                    }
        
        # Keyword-based classification for expenses
        for account_code, keywords in self.classification_engine["expense_keywords"].items():
            for keyword in keywords:
                if keyword in description_lower:
                    return {
                        "debit_account": account_code,
                        "credit_account": "1020" if amount > 0 else "2010",
                        "tax_account": "2220",
                        "confidence": "medium",
                        "keyword_matched": keyword
                    }
        
        # Revenue classification
        for keyword in self.classification_engine["revenue_keywords"]:
            if keyword in description_lower:
                return {
                    "debit_account": "1100" if amount > 0 else "1020",
                    "credit_account": "4000",
                    "tax_account": "2220",
                    "confidence": "medium",
                    "keyword_matched": keyword
                }
        
        # Default classification based on amount
        if amount > 0:
            return {
                "debit_account": "1020",  # Cash
                "credit_account": "4100",  # Other Income
                "tax_account": "2220",
                "confidence": "low",
                "reason": "default_positive_amount"
            }
        else:
            return {
                "debit_account": "5100",  # Operating Expenses
                "credit_account": "1020",  # Cash
                "tax_account": "2220",
                "confidence": "low",
                "reason": "default_negative_amount"
            }
    
    def get_account_suggestions(self, partial_name: str) -> List[Dict[str, str]]:
        """
        Get account suggestions based on partial account name or description
        
        Args:
            partial_name: Partial account name or description
            
        Returns:
            List of matching accounts with codes and names
        """
        suggestions = []
        partial_lower = partial_name.lower()
        
        for account_code, account_info in self.standard_coa.items():
            account_name = account_info["name"].lower()
            if partial_lower in account_name or partial_lower in account_code:
                suggestions.append({
                    "code": account_code,
                    "name": account_info["name"],
                    "type": account_info["type"].value,
                    "relevance": "high" if partial_lower in account_name else "medium"
                })
        
        # Sort by relevance and account type
        suggestions.sort(key=lambda x: (x["relevance"] == "low", x["code"]))
        return suggestions[:10]  # Return top 10 suggestions
    
    def validate_account_mapping(self, debit_account: str, credit_account: str) -> Dict[str, Any]:
        """
        Validate if the account mapping follows double-entry rules
        
        Args:
            debit_account: Debit account code
            credit_account: Credit account code
            
        Returns:
            Validation result with any warnings or errors
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        # Check if accounts exist in chart of accounts
        if debit_account not in self.standard_coa:
            validation_result["errors"].append(f"Debit account {debit_account} not found in chart of accounts")
            validation_result["is_valid"] = False
        
        if credit_account not in self.standard_coa:
            validation_result["errors"].append(f"Credit account {credit_account} not found in chart of accounts")
            validation_result["is_valid"] = False
        
        if not validation_result["is_valid"]:
            return validation_result
        
        debit_type = self.standard_coa[debit_account]["type"]
        credit_type = self.standard_coa[credit_account]["type"]
        
        # Check for logical account combinations
        if debit_type == credit_type:
            validation_result["warnings"].append(
                f"Both accounts are {debit_type.value} - verify this is correct"
            )
        
        # Specific validation rules
        if debit_type == AccountType.REVENUE:
            validation_result["warnings"].append(
                "Revenue accounts are typically credited, not debited"
            )
        
        if credit_type == AccountType.EXPENSES:
            validation_result["warnings"].append(
                "Expense accounts are typically debited, not credited"
            )
        
        return validation_result

    def process_template_file(self, file_path: str, template_type: str) -> ProcessingResult:
        """
        Process uploaded template file and perform automated accounting
        
        Args:
            file_path: Path to the uploaded template file
            template_type: Type of template being processed
            
        Returns:
            ProcessingResult with all generated entries and reports
        """
        try:
            logger.info(f"Processing template file: {file_path}, Type: {template_type}")
            
            # Read and validate template
            df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
            
            # Validate template structure
            validation_result = self._validate_template_structure(df, template_type)
            if not validation_result["valid"]:
                return ProcessingResult(
                    success=False,
                    total_entries=0,
                    journal_entries=[],
                    validation_errors=validation_result["errors"],
                    processing_log=["Template validation failed"],
                    generated_reports={},
                    balance_verification=False
                )
            
            # Process transactions based on template type
            if template_type == "merged":
                journal_entries = self._process_merged_template(df)
            else:
                journal_entries = self._process_specific_template(df, template_type)
            
            # Validate double-entry balancing
            balance_check = self._validate_double_entry_balance(journal_entries)
            
            # Generate all financial reports
            reports = self._generate_all_reports(journal_entries)
            
            # Save to database
            self._save_journal_entries(journal_entries)
            
            return ProcessingResult(
                success=True,
                total_entries=len(journal_entries),
                journal_entries=journal_entries,
                validation_errors=[],
                processing_log=["Processing completed successfully"],
                generated_reports=reports,
                balance_verification=balance_check
            )
            
        except Exception as e:
            logger.error(f"Error processing template: {str(e)}")
            return ProcessingResult(
                success=False,
                total_entries=0,
                journal_entries=[],
                validation_errors=[f"Processing error: {str(e)}"],
                processing_log=["Processing failed"],
                generated_reports={},
                balance_verification=False
            )
    
    def _validate_template_structure(self, df: pd.DataFrame, template_type: str) -> Dict[str, Any]:
        """Validate template structure and required columns"""
        
        required_columns = {
            "purchase": ["date", "vendor_name", "invoice_number", "amount", "tax_amount", "description"],
            "sales": ["date", "customer_name", "invoice_number", "amount", "tax_amount", "description"],
            "income": ["date", "source", "amount", "category", "description"],
            "expense": ["date", "vendor", "amount", "category", "description"],
            "credit_note": ["date", "party_name", "original_invoice", "amount", "reason"],
            "debit_note": ["date", "party_name", "original_invoice", "amount", "reason"],
            "merged": ["date", "transaction_type", "party_name", "amount", "description", "account_code"]
        }
        
        if template_type not in required_columns:
            return {"valid": False, "errors": [f"Unknown template type: {template_type}"]}
        
        missing_columns = []
        for col in required_columns[template_type]:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            return {"valid": False, "errors": [f"Missing required columns: {', '.join(missing_columns)}"]}
        
        return {"valid": True, "errors": []}
    
    def _process_merged_template(self, df: pd.DataFrame) -> List[AccountingEntry]:
        """Process merged template with multiple transaction types"""
        journal_entries = []
        
        for _, row in df.iterrows():
            try:
                transaction_type = TransactionType(row['transaction_type'].lower())
                
                if transaction_type == TransactionType.PURCHASE:
                    entries = self._create_purchase_entries(row)
                elif transaction_type == TransactionType.SALES:
                    entries = self._create_sales_entries(row)
                elif transaction_type == TransactionType.INCOME:
                    entries = self._create_income_entries(row)
                elif transaction_type == TransactionType.EXPENSE:
                    entries = self._create_expense_entries(row)
                elif transaction_type == TransactionType.CREDIT_NOTE:
                    entries = self._create_credit_note_entries(row)
                elif transaction_type == TransactionType.DEBIT_NOTE:
                    entries = self._create_debit_note_entries(row)
                else:
                    entries = self._create_generic_entries(row)
                
                journal_entries.extend(entries)
                
            except Exception as e:
                logger.error(f"Error processing row: {str(e)}")
                continue
        
        return journal_entries
    
    def _process_specific_template(self, df: pd.DataFrame, template_type: str) -> List[AccountingEntry]:
        """Process specific template type"""
        journal_entries = []
        
        for _, row in df.iterrows():
            try:
                if template_type == "purchase":
                    entries = self._create_purchase_entries(row)
                elif template_type == "sales":
                    entries = self._create_sales_entries(row)
                elif template_type == "income":
                    entries = self._create_income_entries(row)
                elif template_type == "expense":
                    entries = self._create_expense_entries(row)
                elif template_type == "credit_note":
                    entries = self._create_credit_note_entries(row)
                elif template_type == "debit_note":
                    entries = self._create_debit_note_entries(row)
                else:
                    entries = []
                
                journal_entries.extend(entries)
                
            except Exception as e:
                logger.error(f"Error processing row: {str(e)}")
                continue
        
        return journal_entries
    
    def _create_purchase_entries(self, row) -> List[AccountingEntry]:
        """Create journal entries for purchase transactions with intelligent classification"""
        entries = []
        
        # Parse amounts
        amount = Decimal(str(row['amount']))
        tax_amount = Decimal(str(row.get('tax_amount', 0)))
        total_amount = amount + tax_amount
        
        # Use intelligent classification for account selection
        description = str(row.get('description', ''))
        classification = self.classify_transaction(description, float(amount), "purchase_template")
        
        # Get account details from classification
        debit_account = classification.get("debit_account", "1200")
        credit_account = classification.get("credit_account", "2010")
        
        # Dr. Purchases/Expense Account (using intelligent classification)
        debit_account_info = self.standard_coa.get(debit_account, {"name": "Inventory"})
        entries.append(AccountingEntry(
            account_code=debit_account,
            account_name=debit_account_info["name"],
            debit_amount=amount,
            credit_amount=Decimal('0'),
            description=f"Purchase from {row.get('vendor_name', 'Vendor')} - {description}",
            reference=row.get('invoice_number', 'N/A'),
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.PURCHASE
        ))
        
        # Dr. Tax Account (if applicable)
        if tax_amount > 0:
            entries.append(AccountingEntry(
                account_code="1300",
                account_name="Input Tax Credit",
                debit_amount=tax_amount,
                credit_amount=Decimal('0'),
                description=f"Tax on purchase from {row['vendor_name']}",
                reference=row['invoice_number'],
                transaction_date=pd.to_datetime(row['date']),
                transaction_type=TransactionType.PURCHASE
            ))
        
        # Cr. Accounts Payable (using intelligent classification)
        credit_account_info = self.standard_coa.get(credit_account, {"name": "Accounts Payable"})
        entries.append(AccountingEntry(
            account_code=credit_account,
            account_name=credit_account_info["name"],
            debit_amount=Decimal('0'),
            credit_amount=total_amount,
            description=f"Amount payable to {row.get('vendor_name', 'Vendor')}",
            reference=row.get('invoice_number', 'N/A'),
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.PURCHASE
        ))
        
        return entries
    
    def _create_sales_entries(self, row) -> List[AccountingEntry]:
        """Create journal entries for sales transactions"""
        entries = []
        
        # Parse amounts
        amount = Decimal(str(row['amount']))
        tax_amount = Decimal(str(row.get('tax_amount', 0)))
        total_amount = amount + tax_amount
        
        # Dr. Accounts Receivable
        entries.append(AccountingEntry(
            account_code="1110",
            account_name="Trade Receivables",
            debit_amount=total_amount,
            credit_amount=Decimal('0'),
            description=f"Sale to {row['customer_name']} - {row['description']}",
            reference=row['invoice_number'],
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.SALES
        ))
        
        # Cr. Sales Revenue
        entries.append(AccountingEntry(
            account_code="4010",
            account_name="Product Sales",
            debit_amount=Decimal('0'),
            credit_amount=amount,
            description=f"Sale to {row['customer_name']}",
            reference=row['invoice_number'],
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.SALES
        ))
        
        # Cr. Tax Payable (if applicable)
        if tax_amount > 0:
            entries.append(AccountingEntry(
                account_code="2220",
                account_name="GST Payable",
                debit_amount=Decimal('0'),
                credit_amount=tax_amount,
                description=f"Tax on sale to {row['customer_name']}",
                reference=row['invoice_number'],
                transaction_date=pd.to_datetime(row['date']),
                transaction_type=TransactionType.SALES
            ))
        
        return entries
    
    def _create_income_entries(self, row) -> List[AccountingEntry]:
        """Create journal entries for income transactions"""
        entries = []
        
        amount = Decimal(str(row['amount']))
        
        # Dr. Cash/Bank Account
        entries.append(AccountingEntry(
            account_code="1020",
            account_name="Bank Account - Current",
            debit_amount=amount,
            credit_amount=Decimal('0'),
            description=f"Income from {row['source']} - {row['description']}",
            reference=f"INC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.INCOME
        ))
        
        # Cr. Income Account
        income_account = self._get_income_account(row.get('category', 'other'))
        entries.append(AccountingEntry(
            account_code=income_account["code"],
            account_name=income_account["name"],
            debit_amount=Decimal('0'),
            credit_amount=amount,
            description=f"Income from {row['source']}",
            reference=f"INC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.INCOME
        ))
        
        return entries
    
    def _create_expense_entries(self, row) -> List[AccountingEntry]:
        """Create journal entries for expense transactions"""
        entries = []
        
        amount = Decimal(str(row['amount']))
        
        # Dr. Expense Account
        expense_account = self._get_expense_account(row.get('category', 'general'))
        entries.append(AccountingEntry(
            account_code=expense_account["code"],
            account_name=expense_account["name"],
            debit_amount=amount,
            credit_amount=Decimal('0'),
            description=f"Expense to {row['vendor']} - {row['description']}",
            reference=f"EXP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.EXPENSE
        ))
        
        # Cr. Cash/Bank Account
        entries.append(AccountingEntry(
            account_code="1020",
            account_name="Bank Account - Current",
            debit_amount=Decimal('0'),
            credit_amount=amount,
            description=f"Payment to {row['vendor']}",
            reference=f"EXP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.EXPENSE
        ))
        
        return entries
    
    def _create_credit_note_entries(self, row) -> List[AccountingEntry]:
        """Create journal entries for credit note transactions"""
        entries = []
        
        amount = Decimal(str(row['amount']))
        
        # Dr. Sales Returns Account
        entries.append(AccountingEntry(
            account_code="4030",
            account_name="Sales Returns",
            debit_amount=amount,
            credit_amount=Decimal('0'),
            description=f"Credit note to {row['party_name']} - {row['reason']}",
            reference=f"CN-{row['original_invoice']}",
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.CREDIT_NOTE
        ))
        
        # Cr. Accounts Receivable
        entries.append(AccountingEntry(
            account_code="1110",
            account_name="Trade Receivables",
            debit_amount=Decimal('0'),
            credit_amount=amount,
            description=f"Credit note adjustment for {row['party_name']}",
            reference=f"CN-{row['original_invoice']}",
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.CREDIT_NOTE
        ))
        
        return entries
    
    def _create_debit_note_entries(self, row) -> List[AccountingEntry]:
        """Create journal entries for debit note transactions"""
        entries = []
        
        amount = Decimal(str(row['amount']))
        
        # Dr. Accounts Receivable
        entries.append(AccountingEntry(
            account_code="1110",
            account_name="Trade Receivables",
            debit_amount=amount,
            credit_amount=Decimal('0'),
            description=f"Debit note to {row['party_name']} - {row['reason']}",
            reference=f"DN-{row['original_invoice']}",
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.DEBIT_NOTE
        ))
        
        # Cr. Additional Income
        entries.append(AccountingEntry(
            account_code="4120",
            account_name="Other Income",
            debit_amount=Decimal('0'),
            credit_amount=amount,
            description=f"Debit note adjustment for {row['party_name']}",
            reference=f"DN-{row['original_invoice']}",
            transaction_date=pd.to_datetime(row['date']),
            transaction_type=TransactionType.DEBIT_NOTE
        ))
        
        return entries
    
    def _create_generic_entries(self, row) -> List[AccountingEntry]:
        """Create generic journal entries based on account codes"""
        entries = []
        
        amount = Decimal(str(row['amount']))
        account_code = row.get('account_code', '1020')
        
        # Determine if this is a debit or credit based on account type
        account_info = self.standard_coa.get(account_code, {"name": "Unknown Account", "type": AccountType.ASSETS})
        
        if account_info["type"] in [AccountType.ASSETS, AccountType.EXPENSES]:
            # Normal debit balance accounts
            entries.append(AccountingEntry(
                account_code=account_code,
                account_name=account_info["name"],
                debit_amount=amount,
                credit_amount=Decimal('0'),
                description=row['description'],
                reference=f"GEN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                transaction_date=pd.to_datetime(row['date']),
                transaction_type=TransactionType.ADJUSTMENT
            ))
            
            # Balancing credit entry
            entries.append(AccountingEntry(
                account_code="1020",
                account_name="Bank Account - Current",
                debit_amount=Decimal('0'),
                credit_amount=amount,
                description=f"Balancing entry for {row['description']}",
                reference=f"GEN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                transaction_date=pd.to_datetime(row['date']),
                transaction_type=TransactionType.ADJUSTMENT
            ))
        else:
            # Normal credit balance accounts
            entries.append(AccountingEntry(
                account_code="1020",
                account_name="Bank Account - Current",
                debit_amount=amount,
                credit_amount=Decimal('0'),
                description=f"Receipt for {row['description']}",
                reference=f"GEN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                transaction_date=pd.to_datetime(row['date']),
                transaction_type=TransactionType.ADJUSTMENT
            ))
            
            entries.append(AccountingEntry(
                account_code=account_code,
                account_name=account_info["name"],
                debit_amount=Decimal('0'),
                credit_amount=amount,
                description=row['description'],
                reference=f"GEN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                transaction_date=pd.to_datetime(row['date']),
                transaction_type=TransactionType.ADJUSTMENT
            ))
        
        return entries
    
    def _get_income_account(self, category: str) -> Dict[str, str]:
        """Get appropriate income account based on category"""
        income_mapping = {
            'sales': {"code": "4010", "name": "Product Sales"},
            'service': {"code": "4020", "name": "Service Revenue"},
            'interest': {"code": "4110", "name": "Interest Income"},
            'rental': {"code": "4120", "name": "Rental Income"},
            'other': {"code": "4100", "name": "Other Income"}
        }
        return income_mapping.get(category.lower(), income_mapping['other'])
    
    def _get_expense_account(self, category: str) -> Dict[str, str]:
        """Get appropriate expense account based on category"""
        expense_mapping = {
            'salary': {"code": "5110", "name": "Salaries and Wages"},
            'rent': {"code": "5120", "name": "Rent Expense"},
            'utilities': {"code": "5130", "name": "Utilities Expense"},
            'office': {"code": "5140", "name": "Office Supplies"},
            'marketing': {"code": "5150", "name": "Marketing Expense"},
            'professional': {"code": "5160", "name": "Professional Fees"},
            'interest': {"code": "5210", "name": "Interest Expense"},
            'bank': {"code": "5220", "name": "Bank Charges"},
            'general': {"code": "5100", "name": "General Expenses"}
        }
        return expense_mapping.get(category.lower(), expense_mapping['general'])
    
    def _validate_double_entry_balance(self, journal_entries: List[AccountingEntry]) -> bool:
        """Validate that total debits equal total credits"""
        total_debits = sum(entry.debit_amount for entry in journal_entries)
        total_credits = sum(entry.credit_amount for entry in journal_entries)
        
        return abs(total_debits - total_credits) < Decimal('0.01')
    
    def _generate_all_reports(self, journal_entries: List[AccountingEntry]) -> Dict[str, str]:
        """Generate all required financial reports"""
        reports = {}
        
        try:
            # Create reports directory
            import os
            reports_dir = f"reports/automated_accounting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate Journal Report
            reports['journal'] = self._generate_journal_report(journal_entries, reports_dir)
            
            # Generate Ledger Report
            reports['ledger'] = self._generate_ledger_report(journal_entries, reports_dir)
            
            # Generate Trial Balance
            reports['trial_balance'] = self._generate_trial_balance_report(journal_entries, reports_dir)
            
            # Generate P&L Statement
            reports['profit_loss'] = self._generate_profit_loss_report(journal_entries, reports_dir)
            
            # Generate Balance Sheet
            reports['balance_sheet'] = self._generate_balance_sheet_report(journal_entries, reports_dir)
            
            # Generate Cash Flow Statement
            reports['cash_flow'] = self._generate_cash_flow_report(journal_entries, reports_dir)
            
            # Generate Shareholders Report
            reports['shareholders'] = self._generate_shareholders_report(journal_entries, reports_dir)
            
        except Exception as e:
            logger.error(f"Error generating reports: {str(e)}")
            
        return reports
    
    def _generate_journal_report(self, journal_entries: List[AccountingEntry], output_dir: str) -> str:
        """Generate detailed journal entries report"""
        journal_data = []
        
        for entry in journal_entries:
            journal_data.append({
                'Date': entry.transaction_date.strftime('%Y-%m-%d'),
                'Account Code': entry.account_code,
                'Account Name': entry.account_name,
                'Reference': entry.reference,
                'Description': entry.description,
                'Debit Amount': float(entry.debit_amount),
                'Credit Amount': float(entry.credit_amount),
                'Transaction Type': entry.transaction_type.value
            })
        
        df_journal = pd.DataFrame(journal_data)
        
        # Sort by date and reference
        df_journal = df_journal.sort_values(['Date', 'Reference'])
        
        # Save to Excel
        output_path = f"{output_dir}/journal_report.xlsx"
        df_journal.to_excel(output_path, index=False)
        
        return output_path
    
    def _generate_ledger_report(self, journal_entries: List[AccountingEntry], output_dir: str) -> str:
        """Generate ledger summary report"""
        ledger_data = {}
        
        for entry in journal_entries:
            if entry.account_code not in ledger_data:
                ledger_data[entry.account_code] = {
                    'Account Name': entry.account_name,
                    'Debit Total': Decimal('0'),
                    'Credit Total': Decimal('0'),
                    'Balance': Decimal('0'),
                    'Transactions': []
                }
            
            ledger_data[entry.account_code]['Debit Total'] += entry.debit_amount
            ledger_data[entry.account_code]['Credit Total'] += entry.credit_amount
            ledger_data[entry.account_code]['Transactions'].append({
                'Date': entry.transaction_date.strftime('%Y-%m-%d'),
                'Reference': entry.reference,
                'Description': entry.description,
                'Debit': float(entry.debit_amount),
                'Credit': float(entry.credit_amount)
            })
        
        # Calculate balances
        for account_code, data in ledger_data.items():
            data['Balance'] = data['Debit Total'] - data['Credit Total']
        
        # Create summary DataFrame
        summary_data = []
        for account_code, data in ledger_data.items():
            summary_data.append({
                'Account Code': account_code,
                'Account Name': data['Account Name'],
                'Debit Total': float(data['Debit Total']),
                'Credit Total': float(data['Credit Total']),
                'Balance': float(data['Balance'])
            })
        
        df_ledger = pd.DataFrame(summary_data)
        
        # Save to Excel
        output_path = f"{output_dir}/ledger_report.xlsx"
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_ledger.to_excel(writer, sheet_name='Ledger Summary', index=False)
            
            # Add detailed transactions for each account
            for account_code, data in ledger_data.items():
                if data['Transactions']:
                    df_trans = pd.DataFrame(data['Transactions'])
                    sheet_name = f"{account_code}_{data['Account Name'][:20]}"
                    df_trans.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return output_path
    
    def _generate_trial_balance_report(self, journal_entries: List[AccountingEntry], output_dir: str) -> str:
        """Generate trial balance report"""
        account_balances = {}
        
        for entry in journal_entries:
            if entry.account_code not in account_balances:
                account_balances[entry.account_code] = {
                    'Account Name': entry.account_name,
                    'Debit': Decimal('0'),
                    'Credit': Decimal('0')
                }
            
            account_balances[entry.account_code]['Debit'] += entry.debit_amount
            account_balances[entry.account_code]['Credit'] += entry.credit_amount
        
        # Create trial balance data
        trial_balance_data = []
        total_debits = Decimal('0')
        total_credits = Decimal('0')
        
        for account_code, data in account_balances.items():
            balance = data['Debit'] - data['Credit']
            debit_balance = balance if balance > 0 else Decimal('0')
            credit_balance = abs(balance) if balance < 0 else Decimal('0')
            
            trial_balance_data.append({
                'Account Code': account_code,
                'Account Name': data['Account Name'],
                'Debit Balance': float(debit_balance),
                'Credit Balance': float(credit_balance)
            })
            
            total_debits += debit_balance
            total_credits += credit_balance
        
        # Add totals row
        trial_balance_data.append({
            'Account Code': 'TOTAL',
            'Account Name': 'Total',
            'Debit Balance': float(total_debits),
            'Credit Balance': float(total_credits)
        })
        
        df_trial_balance = pd.DataFrame(trial_balance_data)
        
        # Save to Excel
        output_path = f"{output_dir}/trial_balance.xlsx"
        df_trial_balance.to_excel(output_path, index=False)
        
        return output_path
    
    def _generate_profit_loss_report(self, journal_entries: List[AccountingEntry], output_dir: str) -> str:
        """Generate Profit & Loss statement"""
        revenue_accounts = {}
        expense_accounts = {}
        
        for entry in journal_entries:
            account_info = self.standard_coa.get(entry.account_code, {"type": AccountType.ASSETS})
            
            if account_info["type"] == AccountType.REVENUE:
                if entry.account_code not in revenue_accounts:
                    revenue_accounts[entry.account_code] = {
                        'name': entry.account_name,
                        'amount': Decimal('0')
                    }
                revenue_accounts[entry.account_code]['amount'] += entry.credit_amount - entry.debit_amount
            
            elif account_info["type"] == AccountType.EXPENSES:
                if entry.account_code not in expense_accounts:
                    expense_accounts[entry.account_code] = {
                        'name': entry.account_name,
                        'amount': Decimal('0')
                    }
                expense_accounts[entry.account_code]['amount'] += entry.debit_amount - entry.credit_amount
        
        # Create P&L data
        pl_data = []
        
        # Revenue section
        pl_data.append({'Category': 'REVENUE', 'Account': '', 'Amount': ''})
        total_revenue = Decimal('0')
        for account_code, data in revenue_accounts.items():
            pl_data.append({
                'Category': 'Revenue',
                'Account': f"{account_code} - {data['name']}",
                'Amount': float(data['amount'])
            })
            total_revenue += data['amount']
        
        pl_data.append({'Category': 'Total Revenue', 'Account': '', 'Amount': float(total_revenue)})
        pl_data.append({'Category': '', 'Account': '', 'Amount': ''})
        
        # Expense section
        pl_data.append({'Category': 'EXPENSES', 'Account': '', 'Amount': ''})
        total_expenses = Decimal('0')
        for account_code, data in expense_accounts.items():
            pl_data.append({
                'Category': 'Expenses',
                'Account': f"{account_code} - {data['name']}",
                'Amount': float(data['amount'])
            })
            total_expenses += data['amount']
        
        pl_data.append({'Category': 'Total Expenses', 'Account': '', 'Amount': float(total_expenses)})
        pl_data.append({'Category': '', 'Account': '', 'Amount': ''})
        
        # Net Income
        net_income = total_revenue - total_expenses
        pl_data.append({'Category': 'NET INCOME', 'Account': '', 'Amount': float(net_income)})
        
        df_pl = pd.DataFrame(pl_data)
        
        # Save to Excel
        output_path = f"{output_dir}/profit_loss_statement.xlsx"
        df_pl.to_excel(output_path, index=False)
        
        return output_path
    
    def _generate_balance_sheet_report(self, journal_entries: List[AccountingEntry], output_dir: str) -> str:
        """Generate Balance Sheet"""
        assets = {}
        liabilities = {}
        equity = {}
        
        for entry in journal_entries:
            account_info = self.standard_coa.get(entry.account_code, {"type": AccountType.ASSETS})
            balance = entry.debit_amount - entry.credit_amount
            
            if account_info["type"] == AccountType.ASSETS:
                if entry.account_code not in assets:
                    assets[entry.account_code] = {'name': entry.account_name, 'amount': Decimal('0')}
                assets[entry.account_code]['amount'] += balance
            
            elif account_info["type"] == AccountType.LIABILITIES:
                if entry.account_code not in liabilities:
                    liabilities[entry.account_code] = {'name': entry.account_name, 'amount': Decimal('0')}
                liabilities[entry.account_code]['amount'] += -balance  # Liabilities are credit balance
            
            elif account_info["type"] == AccountType.EQUITY:
                if entry.account_code not in equity:
                    equity[entry.account_code] = {'name': entry.account_name, 'amount': Decimal('0')}
                equity[entry.account_code]['amount'] += -balance  # Equity is credit balance
        
        # Create Balance Sheet data
        bs_data = []
        
        # Assets section
        bs_data.append({'Category': 'ASSETS', 'Account': '', 'Amount': ''})
        total_assets = Decimal('0')
        for account_code, data in assets.items():
            if data['amount'] != 0:
                bs_data.append({
                    'Category': 'Assets',
                    'Account': f"{account_code} - {data['name']}",
                    'Amount': float(data['amount'])
                })
                total_assets += data['amount']
        
        bs_data.append({'Category': 'Total Assets', 'Account': '', 'Amount': float(total_assets)})
        bs_data.append({'Category': '', 'Account': '', 'Amount': ''})
        
        # Liabilities section
        bs_data.append({'Category': 'LIABILITIES', 'Account': '', 'Amount': ''})
        total_liabilities = Decimal('0')
        for account_code, data in liabilities.items():
            if data['amount'] != 0:
                bs_data.append({
                    'Category': 'Liabilities',
                    'Account': f"{account_code} - {data['name']}",
                    'Amount': float(data['amount'])
                })
                total_liabilities += data['amount']
        
        bs_data.append({'Category': 'Total Liabilities', 'Account': '', 'Amount': float(total_liabilities)})
        bs_data.append({'Category': '', 'Account': '', 'Amount': ''})
        
        # Equity section
        bs_data.append({'Category': 'EQUITY', 'Account': '', 'Amount': ''})
        total_equity = Decimal('0')
        for account_code, data in equity.items():
            if data['amount'] != 0:
                bs_data.append({
                    'Category': 'Equity',
                    'Account': f"{account_code} - {data['name']}",
                    'Amount': float(data['amount'])
                })
                total_equity += data['amount']
        
        bs_data.append({'Category': 'Total Equity', 'Account': '', 'Amount': float(total_equity)})
        bs_data.append({'Category': '', 'Account': '', 'Amount': ''})
        
        # Total Liabilities and Equity
        total_liab_equity = total_liabilities + total_equity
        bs_data.append({'Category': 'TOTAL LIABILITIES & EQUITY', 'Account': '', 'Amount': float(total_liab_equity)})
        
        df_bs = pd.DataFrame(bs_data)
        
        # Save to Excel
        output_path = f"{output_dir}/balance_sheet.xlsx"
        df_bs.to_excel(output_path, index=False)
        
        return output_path
    
    def _generate_cash_flow_report(self, journal_entries: List[AccountingEntry], output_dir: str) -> str:
        """Generate Cash Flow Statement"""
        cash_flows = {
            'operating': [],
            'investing': [],
            'financing': []
        }
        
        for entry in journal_entries:
            if entry.account_code in ['1020', '1030', '1010']:  # Cash accounts
                cash_flow_item = {
                    'description': entry.description,
                    'amount': entry.debit_amount - entry.credit_amount,
                    'date': entry.transaction_date
                }
                
                # Classify based on transaction type or account
                if entry.transaction_type in [TransactionType.SALES, TransactionType.PURCHASE, TransactionType.EXPENSE]:
                    cash_flows['operating'].append(cash_flow_item)
                elif entry.transaction_type == TransactionType.TRANSFER:
                    cash_flows['financing'].append(cash_flow_item)
                else:
                    cash_flows['operating'].append(cash_flow_item)
        
        # Create Cash Flow data
        cf_data = []
        
        # Operating Activities
        cf_data.append({'Category': 'OPERATING ACTIVITIES', 'Description': '', 'Amount': ''})
        operating_total = Decimal('0')
        for item in cash_flows['operating']:
            cf_data.append({
                'Category': 'Operating',
                'Description': item['description'],
                'Amount': float(item['amount'])
            })
            operating_total += item['amount']
        
        cf_data.append({'Category': 'Net Cash from Operating Activities', 'Description': '', 'Amount': float(operating_total)})
        cf_data.append({'Category': '', 'Description': '', 'Amount': ''})
        
        # Investing Activities
        cf_data.append({'Category': 'INVESTING ACTIVITIES', 'Description': '', 'Amount': ''})
        investing_total = Decimal('0')
        for item in cash_flows['investing']:
            cf_data.append({
                'Category': 'Investing',
                'Description': item['description'],
                'Amount': float(item['amount'])
            })
            investing_total += item['amount']
        
        cf_data.append({'Category': 'Net Cash from Investing Activities', 'Description': '', 'Amount': float(investing_total)})
        cf_data.append({'Category': '', 'Description': '', 'Amount': ''})
        
        # Financing Activities
        cf_data.append({'Category': 'FINANCING ACTIVITIES', 'Description': '', 'Amount': ''})
        financing_total = Decimal('0')
        for item in cash_flows['financing']:
            cf_data.append({
                'Category': 'Financing',
                'Description': item['description'],
                'Amount': float(item['amount'])
            })
            financing_total += item['amount']
        
        cf_data.append({'Category': 'Net Cash from Financing Activities', 'Description': '', 'Amount': float(financing_total)})
        cf_data.append({'Category': '', 'Description': '', 'Amount': ''})
        
        # Net Change in Cash
        net_change = operating_total + investing_total + financing_total
        cf_data.append({'Category': 'NET CHANGE IN CASH', 'Description': '', 'Amount': float(net_change)})
        
        df_cf = pd.DataFrame(cf_data)
        
        # Save to Excel
        output_path = f"{output_dir}/cash_flow_statement.xlsx"
        df_cf.to_excel(output_path, index=False)
        
        return output_path
    
    def _generate_shareholders_report(self, journal_entries: List[AccountingEntry], output_dir: str) -> str:
        """Generate Shareholders' Equity Report"""
        equity_movements = []
        
        for entry in journal_entries:
            account_info = self.standard_coa.get(entry.account_code, {"type": AccountType.ASSETS})
            
            if account_info["type"] == AccountType.EQUITY:
                equity_movements.append({
                    'Date': entry.transaction_date.strftime('%Y-%m-%d'),
                    'Account': f"{entry.account_code} - {entry.account_name}",
                    'Description': entry.description,
                    'Debit': float(entry.debit_amount),
                    'Credit': float(entry.credit_amount),
                    'Reference': entry.reference
                })
        
        # Calculate equity summary
        equity_summary = {}
        for entry in journal_entries:
            account_info = self.standard_coa.get(entry.account_code, {"type": AccountType.ASSETS})
            
            if account_info["type"] == AccountType.EQUITY:
                if entry.account_code not in equity_summary:
                    equity_summary[entry.account_code] = {
                        'name': entry.account_name,
                        'balance': Decimal('0')
                    }
                equity_summary[entry.account_code]['balance'] += entry.credit_amount - entry.debit_amount
        
        # Create summary data
        summary_data = []
        total_equity = Decimal('0')
        
        for account_code, data in equity_summary.items():
            summary_data.append({
                'Account Code': account_code,
                'Account Name': data['name'],
                'Balance': float(data['balance'])
            })
            total_equity += data['balance']
        
        summary_data.append({
            'Account Code': 'TOTAL',
            'Account Name': 'Total Shareholders Equity',
            'Balance': float(total_equity)
        })
        
        # Save to Excel
        output_path = f"{output_dir}/shareholders_report.xlsx"
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Equity Summary', index=False)
            
            # Detailed movements
            if equity_movements:
                pd.DataFrame(equity_movements).to_excel(writer, sheet_name='Equity Movements', index=False)
        
        return output_path
    
    def _save_journal_entries(self, journal_entries: List[AccountingEntry]):
        """Save journal entries to database"""
        try:
            for entry in journal_entries:
                # Find or create account
                account = ChartOfAccount.query.filter_by(
                    company_id=self.company_id,
                    account_code=entry.account_code
                ).first()
                
                if not account:
                    account = ChartOfAccount(
                        company_id=self.company_id,
                        account_code=entry.account_code,
                        account_name=entry.account_name,
                        account_type=entry.transaction_type.value
                    )
                    db.session.add(account)
                    db.session.flush()
                
                # Create journal entry
                journal_entry = JournalEntry(
                    company_id=self.company_id,
                    account_id=account.id,
                    created_by=self.user_id,
                    entry_date=entry.transaction_date,
                    description=entry.description,
                    reference_number=entry.reference,
                    debit_amount=float(entry.debit_amount),
                    credit_amount=float(entry.credit_amount),
                    is_posted=True
                )
                db.session.add(journal_entry)
            
            db.session.commit()
            logger.info(f"Saved {len(journal_entries)} journal entries to database")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving journal entries: {str(e)}")
            raise
    
    def create_manual_journal_entry(self, entries: List[Dict[str, Any]]) -> bool:
        """Create manual journal entry"""
        try:
            total_debits = sum(Decimal(str(entry.get('debit_amount', 0))) for entry in entries)
            total_credits = sum(Decimal(str(entry.get('credit_amount', 0))) for entry in entries)
            
            # Validate double-entry balance
            if abs(total_debits - total_credits) > Decimal('0.01'):
                raise ValueError("Journal entry is not balanced")
            
            # Create journal entries
            for entry_data in entries:
                account = ChartOfAccount.query.filter_by(
                    company_id=self.company_id,
                    account_code=entry_data['account_code']
                ).first()
                
                if not account:
                    raise ValueError(f"Account {entry_data['account_code']} not found")
                
                journal_entry = JournalEntry(
                    company_id=self.company_id,
                    account_id=account.id,
                    created_by=self.user_id,
                    entry_date=datetime.strptime(entry_data['date'], '%Y-%m-%d'),
                    description=entry_data['description'],
                    reference_number=entry_data.get('reference', f"MAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    debit_amount=float(entry_data.get('debit_amount', 0)),
                    credit_amount=float(entry_data.get('credit_amount', 0)),
                    is_posted=True
                )
                db.session.add(journal_entry)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating manual journal entry: {str(e)}")
            return False
    
    def get_chart_of_accounts(self) -> List[Dict[str, Any]]:
        """Get chart of accounts for the company"""
        accounts = ChartOfAccount.query.filter_by(
            company_id=self.company_id,
            is_active=True
        ).all()
        
        return [
            {
                'id': account.id,
                'account_code': account.account_code,
                'account_name': account.account_name,
                'account_type': account.account_type,
                'parent_account_id': account.parent_account_id
            }
            for account in accounts
        ]
    
    def setup_standard_chart_of_accounts(self):
        """Setup standard chart of accounts for the company"""
        try:
            for account_code, account_info in self.standard_coa.items():
                existing_account = ChartOfAccount.query.filter_by(
                    company_id=self.company_id,
                    account_code=account_code
                ).first()
                
                if not existing_account:
                    parent_id = None
                    if account_info.get('parent'):
                        parent_account = ChartOfAccount.query.filter_by(
                            company_id=self.company_id,
                            account_code=account_info['parent']
                        ).first()
                        if parent_account:
                            parent_id = parent_account.id
                    
                    account = ChartOfAccount(
                        company_id=self.company_id,
                        account_code=account_code,
                        account_name=account_info['name'],
                        account_type=account_info['type'].value if hasattr(account_info['type'], 'value') else str(account_info['type']),
                        parent_account_id=parent_id
                    )
                    db.session.add(account)
            
            db.session.commit()
            logger.info(f"Standard chart of accounts created for company {self.company_id}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting up chart of accounts: {str(e)}")
            raise
    
    def generate_all_reports(self) -> Dict[str, Any]:
        """
        Generate comprehensive financial reports package including MIS analysis
        """
        try:
            logger.info("Starting comprehensive financial reports generation")
            
            # Generate individual financial reports
            reports_data = {
                'journal': self.generate_journal_report(),
                'ledger': self.generate_ledger_report(), 
                'trial_balance': self.generate_trial_balance(),
                'profit_loss': self.generate_profit_loss_statement(),
                'balance_sheet': self.generate_balance_sheet(),
                'cash_flow': self.generate_cash_flow_statement(),
                'shareholders_equity': self.generate_shareholders_equity_statement()
            }
            
            # Generate MIS Report with accounting validation and ratio analysis
            mis_service = MISReportService(self.company_id, self.user_id)
            reports_data['mis_report'] = mis_service.generate_mis_report(reports_data)
            
            # Add generation metadata
            reports_data['metadata'] = {
                'generation_date': datetime.now().isoformat(),
                'company_id': self.company_id,
                'user_id': self.user_id,
                'total_reports': len(reports_data) - 1,  # Excluding metadata
                'includes_mis': True
            }
            
            logger.info("All financial reports generated successfully")
            return reports_data
            
        except Exception as e:
            logger.error(f"Error generating comprehensive reports: {str(e)}")
            raise
    
    def generate_journal_report(self) -> Dict[str, Any]:
        """Generate journal entries report"""
        try:
            entries = JournalEntry.query.filter_by(company_id=self.company_id).all()
            
            journal_data = {
                'report_title': 'Journal Entries Report',
                'generation_date': datetime.now().isoformat(),
                'entries': [],
                'summary': {
                    'total_entries': len(entries),
                    'total_debits': 0,
                    'total_credits': 0
                }
            }
            
            for entry in entries:
                entry_data = {
                    'entry_id': entry.id,
                    'date': entry.transaction_date.isoformat() if entry.transaction_date else '',
                    'description': entry.description or '',
                    'account_code': entry.account_code or '',
                    'account_name': entry.account_name or '',
                    'debit_amount': float(entry.debit_amount or 0),
                    'credit_amount': float(entry.credit_amount or 0),
                    'transaction_type': entry.transaction_type or ''
                }
                journal_data['entries'].append(entry_data)
                journal_data['summary']['total_debits'] += entry_data['debit_amount']
                journal_data['summary']['total_credits'] += entry_data['credit_amount']
            
            return journal_data
            
        except Exception as e:
            logger.error(f"Error generating journal report: {str(e)}")
            return {'error': str(e)}
    
    def generate_ledger_report(self) -> Dict[str, Any]:
        """Generate ledger accounts report"""
        try:
            accounts = ChartOfAccount.query.filter_by(company_id=self.company_id).all()
            ledger_data = {
                'report_title': 'Ledger Accounts Report',
                'generation_date': datetime.now().isoformat(),
                'accounts': []
            }
            
            for account in accounts:
                # Get all entries for this account
                entries = JournalEntry.query.filter_by(
                    company_id=self.company_id,
                    account_code=account.account_code
                ).all()
                
                balance = 0
                account_entries = []
                
                for entry in entries:
                    debit = float(entry.debit_amount or 0)
                    credit = float(entry.credit_amount or 0)
                    balance += debit - credit
                    
                    account_entries.append({
                        'date': entry.transaction_date.isoformat() if entry.transaction_date else '',
                        'description': entry.description or '',
                        'debit': debit,
                        'credit': credit,
                        'balance': balance
                    })
                
                ledger_data['accounts'].append({
                    'account_code': account.account_code,
                    'account_name': account.account_name,
                    'account_type': account.account_type,
                    'closing_balance': balance,
                    'entries': account_entries
                })
            
            return ledger_data
            
        except Exception as e:
            logger.error(f"Error generating ledger report: {str(e)}")
            return {'error': str(e)}
    
    def generate_trial_balance(self) -> Dict[str, Any]:
        """Generate trial balance"""
        try:
            accounts = ChartOfAccount.query.filter_by(company_id=self.company_id).all()
            trial_balance_data = {
                'report_title': 'Trial Balance',
                'generation_date': datetime.now().isoformat(),
                'accounts': [],
                'totals': {
                    'total_debits': 0,
                    'total_credits': 0
                }
            }
            
            for account in accounts:
                # Calculate balance for each account
                entries = JournalEntry.query.filter_by(
                    company_id=self.company_id,
                    account_code=account.account_code
                ).all()
                
                total_debits = sum(float(e.debit_amount or 0) for e in entries)
                total_credits = sum(float(e.credit_amount or 0) for e in entries)
                net_balance = total_debits - total_credits
                
                debit_balance = net_balance if net_balance > 0 else 0
                credit_balance = abs(net_balance) if net_balance < 0 else 0
                
                trial_balance_data['accounts'].append({
                    'account_code': account.account_code,
                    'account_name': account.account_name,
                    'account_type': account.account_type,
                    'debit_balance': debit_balance,
                    'credit_balance': credit_balance
                })
                
                trial_balance_data['totals']['total_debits'] += debit_balance
                trial_balance_data['totals']['total_credits'] += credit_balance
            
            return trial_balance_data
            
        except Exception as e:
            logger.error(f"Error generating trial balance: {str(e)}")
            return {'error': str(e)}
    
    def generate_profit_loss_statement(self) -> Dict[str, Any]:
        """Generate profit and loss statement"""
        try:
            # Get revenue and expense accounts
            accounts = ChartOfAccount.query.filter_by(company_id=self.company_id).all()
            
            pl_data = {
                'report_title': 'Profit & Loss Statement',
                'generation_date': datetime.now().isoformat(),
                'revenue': {'accounts': [], 'total': 0},
                'expenses': {'accounts': [], 'total': 0},
                'cost_of_goods_sold': 0,
                'gross_profit': 0,
                'net_profit': 0
            }
            
            for account in accounts:
                entries = JournalEntry.query.filter_by(
                    company_id=self.company_id,
                    account_code=account.account_code
                ).all()
                
                total_debits = sum(float(e.debit_amount or 0) for e in entries)
                total_credits = sum(float(e.credit_amount or 0) for e in entries)
                
                if account.account_type == 'revenue':
                    balance = total_credits - total_debits
                    pl_data['revenue']['accounts'].append({
                        'account_code': account.account_code,
                        'account_name': account.account_name,
                        'amount': balance
                    })
                    pl_data['revenue']['total'] += balance
                
                elif account.account_type == 'expenses':
                    balance = total_debits - total_credits
                    pl_data['expenses']['accounts'].append({
                        'account_code': account.account_code,
                        'account_name': account.account_name,
                        'amount': balance
                    })
                    pl_data['expenses']['total'] += balance
            
            pl_data['gross_profit'] = pl_data['revenue']['total'] - pl_data['cost_of_goods_sold']
            pl_data['net_profit'] = pl_data['revenue']['total'] - pl_data['expenses']['total']
            
            return pl_data
            
        except Exception as e:
            logger.error(f"Error generating P&L statement: {str(e)}")
            return {'error': str(e)}
    
    def generate_balance_sheet(self) -> Dict[str, Any]:
        """Generate balance sheet"""
        try:
            accounts = ChartOfAccount.query.filter_by(company_id=self.company_id).all()
            
            balance_sheet_data = {
                'report_title': 'Balance Sheet',
                'generation_date': datetime.now().isoformat(),
                'assets': {'current_assets': {'accounts': [], 'total': 0}, 'fixed_assets': {'accounts': [], 'total': 0}, 'total': 0},
                'liabilities': {'current_liabilities': {'accounts': [], 'total': 0}, 'long_term_liabilities': {'accounts': [], 'total': 0}, 'total': 0},
                'equity': {'accounts': [], 'total': 0}
            }
            
            for account in accounts:
                entries = JournalEntry.query.filter_by(
                    company_id=self.company_id,
                    account_code=account.account_code
                ).all()
                
                total_debits = sum(float(e.debit_amount or 0) for e in entries)
                total_credits = sum(float(e.credit_amount or 0) for e in entries)
                
                if account.account_type == 'assets':
                    balance = total_debits - total_credits
                    asset_info = {
                        'account_code': account.account_code,
                        'account_name': account.account_name,
                        'amount': balance
                    }
                    
                    # Categorize as current or fixed assets (simple logic)
                    if 'cash' in account.account_name.lower() or 'receivable' in account.account_name.lower():
                        balance_sheet_data['assets']['current_assets']['accounts'].append(asset_info)
                        balance_sheet_data['assets']['current_assets']['total'] += balance
                    else:
                        balance_sheet_data['assets']['fixed_assets']['accounts'].append(asset_info)
                        balance_sheet_data['assets']['fixed_assets']['total'] += balance
                    
                    balance_sheet_data['assets']['total'] += balance
                
                elif account.account_type == 'liabilities':
                    balance = total_credits - total_debits
                    liability_info = {
                        'account_code': account.account_code,
                        'account_name': account.account_name,
                        'amount': balance
                    }
                    
                    # Categorize as current or long-term liabilities
                    if 'payable' in account.account_name.lower() or 'accrued' in account.account_name.lower():
                        balance_sheet_data['liabilities']['current_liabilities']['accounts'].append(liability_info)
                        balance_sheet_data['liabilities']['current_liabilities']['total'] += balance
                    else:
                        balance_sheet_data['liabilities']['long_term_liabilities']['accounts'].append(liability_info)
                        balance_sheet_data['liabilities']['long_term_liabilities']['total'] += balance
                    
                    balance_sheet_data['liabilities']['total'] += balance
                
                elif account.account_type == 'equity':
                    balance = total_credits - total_debits
                    balance_sheet_data['equity']['accounts'].append({
                        'account_code': account.account_code,
                        'account_name': account.account_name,
                        'amount': balance
                    })
                    balance_sheet_data['equity']['total'] += balance
            
            return balance_sheet_data
            
        except Exception as e:
            logger.error(f"Error generating balance sheet: {str(e)}")
            return {'error': str(e)}
    
    def generate_cash_flow_statement(self) -> Dict[str, Any]:
        """Generate cash flow statement"""
        try:
            cash_flow_data = {
                'report_title': 'Cash Flow Statement',
                'generation_date': datetime.now().isoformat(),
                'operating': {'activities': [], 'net_cash': 0},
                'investing': {'activities': [], 'net_cash': 0},
                'financing': {'activities': [], 'net_cash': 0},
                'net_cash_flow': 0
            }
            
            # Get cash-related entries
            cash_entries = JournalEntry.query.filter(
                JournalEntry.company_id == self.company_id,
                JournalEntry.account_name.ilike('%cash%')
            ).all()
            
            for entry in cash_entries:
                activity = {
                    'description': entry.description or '',
                    'amount': float(entry.debit_amount or 0) - float(entry.credit_amount or 0),
                    'date': entry.transaction_date.isoformat() if entry.transaction_date else ''
                }
                
                # Simple categorization logic
                if any(word in entry.description.lower() for word in ['sale', 'revenue', 'collection', 'payment'] if entry.description):
                    cash_flow_data['operating']['activities'].append(activity)
                    cash_flow_data['operating']['net_cash'] += activity['amount']
                elif any(word in entry.description.lower() for word in ['asset', 'equipment', 'investment'] if entry.description):
                    cash_flow_data['investing']['activities'].append(activity)
                    cash_flow_data['investing']['net_cash'] += activity['amount']
                else:
                    cash_flow_data['financing']['activities'].append(activity)
                    cash_flow_data['financing']['net_cash'] += activity['amount']
            
            cash_flow_data['net_cash_flow'] = (
                cash_flow_data['operating']['net_cash'] +
                cash_flow_data['investing']['net_cash'] +
                cash_flow_data['financing']['net_cash']
            )
            
            return cash_flow_data
            
        except Exception as e:
            logger.error(f"Error generating cash flow statement: {str(e)}")
            return {'error': str(e)}
    
    def generate_shareholders_equity_statement(self) -> Dict[str, Any]:
        """Generate shareholders' equity statement"""
        try:
            equity_accounts = ChartOfAccount.query.filter_by(
                company_id=self.company_id,
                account_type='equity'
            ).all()
            
            equity_data = {
                'report_title': 'Statement of Shareholders\' Equity',
                'generation_date': datetime.now().isoformat(),
                'beginning_balance': 0,
                'movements': [],
                'ending_balance': 0
            }
            
            total_equity = 0
            
            for account in equity_accounts:
                entries = JournalEntry.query.filter_by(
                    company_id=self.company_id,
                    account_code=account.account_code
                ).all()
                
                account_balance = sum(float(e.credit_amount or 0) - float(e.debit_amount or 0) for e in entries)
                total_equity += account_balance
                
                equity_data['movements'].append({
                    'account_name': account.account_name,
                    'amount': account_balance,
                    'type': 'Equity Contribution' if account_balance > 0 else 'Equity Distribution'
                })
            
            equity_data['ending_balance'] = total_equity
            
            return equity_data
            
        except Exception as e:
            logger.error(f"Error generating shareholders' equity statement: {str(e)}")
            return {'error': str(e)}