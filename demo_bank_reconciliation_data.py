"""
Demo Bank Reconciliation Data Generator
Creates realistic test data for bank reconciliation dashboard demonstration
"""
import json
import random
from datetime import datetime, timedelta

def generate_demo_bank_transactions():
    """Generate realistic bank transaction data"""
    transactions = []
    base_date = datetime.now() - timedelta(days=30)
    
    # Sample transaction descriptions and amounts
    transaction_types = [
        {"desc": "NEFT CR ABC TECHNOLOGIES INV2024-001 SOFTWARE PAYMENT", "amount": 50000, "type": "credit"},
        {"desc": "UPI DR XYZ OFFICE BILL5678 FURNITURE", "amount": -12500, "type": "debit"},
        {"desc": "SALARY TRANSFER EMPLOYEES JAN2024", "amount": -125000, "type": "debit"},
        {"desc": "NEFT CR CLIENT PAYMENT INV2024-002", "amount": 75000, "type": "credit"},
        {"desc": "RTGS DR RENT PAYMENT JAN2024", "amount": -25000, "type": "debit"},
        {"desc": "UPI CR CONSULTING SERVICES PAYMENT", "amount": 35000, "type": "credit"},
        {"desc": "IMPS DR UTILITIES ELECTRICITY BILL", "amount": -8500, "type": "debit"},
        {"desc": "NEFT CR PRODUCT SALES INVOICE2024-003", "amount": 92000, "type": "credit"},
        {"desc": "CHEQUE DR VENDOR PAYMENT SUPPLIES", "amount": -18000, "type": "debit"},
        {"desc": "UPI DR TRAVEL EXPENSES REIMBURSE", "amount": -5500, "type": "debit"},
        {"desc": "NEFT CR SUBSCRIPTION REVENUE JAN2024", "amount": 45000, "type": "credit"},
        {"desc": "RTGS DR LOAN EMI PAYMENT", "amount": -15000, "type": "debit"},
        {"desc": "UPI CR FREELANCE PAYMENT PROJECT", "amount": 22000, "type": "credit"},
        {"desc": "IMPS DR INSURANCE PREMIUM", "amount": -12000, "type": "debit"},
        {"desc": "BANK CHARGES TRANSACTION FEES", "amount": -250, "type": "debit"},
    ]
    
    # Generate transactions with realistic matching patterns
    for i, tx_template in enumerate(transaction_types):
        date = base_date + timedelta(days=random.randint(0, 30))
        
        # Add some variation to amounts
        amount_variation = random.uniform(0.95, 1.05)
        amount = int(tx_template["amount"] * amount_variation)
        
        # Determine matching status and confidence
        if i < 8:  # First 8 are matched with high confidence
            status = "matched"
            confidence = random.randint(85, 98)
            matched_invoice = f"INV2024-{str(i+1).zfill(3)}"
        elif i < 12:  # Next 4 are unmatched
            status = "unmatched" 
            confidence = random.randint(45, 65)
            matched_invoice = None
        else:  # Last 3 are doubtful/flagged
            status = "doubtful"
            confidence = random.randint(65, 75)
            matched_invoice = f"PARTIAL-{str(i+1).zfill(3)}"
        
        transaction = {
            "id": f"TXN{str(i+1).zfill(4)}",
            "date": date.strftime("%Y-%m-%d"),
            "description": tx_template["desc"],
            "amount": amount,
            "type": tx_template["type"],
            "status": status,
            "confidence": confidence,
            "matched_invoice": matched_invoice,
            "reference": f"REF{random.randint(100000, 999999)}"
        }
        transactions.append(transaction)
    
    return transactions

def generate_demo_invoice_data():
    """Generate realistic invoice data for matching"""
    invoices = []
    base_date = datetime.now() - timedelta(days=45)
    
    invoice_templates = [
        {"client": "ABC Technologies Pvt Ltd", "amount": 50000, "desc": "Software Development Services"},
        {"client": "XYZ Office Supplies", "amount": 12500, "desc": "Office Furniture Purchase"},
        {"client": "Tech Solutions Inc", "amount": 75000, "desc": "Consulting Services Q1"},
        {"client": "Digital Marketing Co", "amount": 35000, "desc": "Marketing Campaign Management"},
        {"client": "Cloud Services Ltd", "amount": 92000, "desc": "Enterprise Software License"},
        {"client": "Professional Services", "amount": 22000, "desc": "Business Process Optimization"},
        {"client": "Training Institute", "amount": 45000, "desc": "Employee Training Program"},
        {"client": "Equipment Rental", "amount": 18000, "desc": "Office Equipment Lease"},
    ]
    
    for i, inv_template in enumerate(invoice_templates):
        date = base_date + timedelta(days=random.randint(0, 40))
        
        invoice = {
            "invoice_number": f"INV2024-{str(i+1).zfill(3)}",
            "date": date.strftime("%Y-%m-%d"),
            "client": inv_template["client"],
            "amount": inv_template["amount"],
            "description": inv_template["desc"],
            "status": "pending" if i >= 8 else "paid",
            "due_date": (date + timedelta(days=30)).strftime("%Y-%m-%d")
        }
        invoices.append(invoice)
    
    return invoices

def generate_reconciliation_statistics():
    """Generate realistic reconciliation statistics"""
    return {
        "total_transactions": 15,
        "ai_matches": 8,
        "manual_matches": 2,
        "unmatched": 4,
        "exceptions": 3,
        "confidence_rate": 87,
        "matched_amount": 389000,
        "unmatched_amount": 61250,
        "flagged_amount": 27250,
        "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_activity_log():
    """Generate realistic user activity log"""
    activities = [
        {"user": "Admin", "action": "manually mapped transaction TXN0009", "type": "manual", "timestamp": "2024-01-15 14:30:00"},
        {"user": "System", "action": "AI auto-matched 8 transactions", "type": "ai", "timestamp": "2024-01-15 14:25:00"},
        {"user": "Accountant", "action": "reviewed exceptions for TXN0013", "type": "manual", "timestamp": "2024-01-15 14:20:00"},
        {"user": "System", "action": "batch reconciliation started", "type": "system", "timestamp": "2024-01-15 14:15:00"},
        {"user": "Admin", "action": "uploaded bank statement file", "type": "system", "timestamp": "2024-01-15 14:10:00"},
        {"user": "System", "action": "confidence threshold updated to 80%", "type": "system", "timestamp": "2024-01-15 14:05:00"},
    ]
    return activities

def generate_exceptions_data():
    """Generate realistic exceptions for review"""
    exceptions = [
        {
            "type": "duplicate",
            "severity": "warning", 
            "description": "Duplicate Transaction: Amount ₹50,000 appears twice on 2024-01-15",
            "transaction_ids": ["TXN0001", "TXN0008"],
            "recommended_action": "Review and merge duplicate entries"
        },
        {
            "type": "currency_mismatch",
            "severity": "info",
            "description": "Currency Mismatch: USD transaction in INR bank account", 
            "transaction_ids": ["TXN0012"],
            "recommended_action": "Verify exchange rate and convert currency"
        },
        {
            "type": "partial_match", 
            "severity": "secondary",
            "description": "Partial Match: Invoice amount differs by ₹500",
            "transaction_ids": ["TXN0013"],
            "recommended_action": "Check for additional charges or adjustments"
        }
    ]
    return exceptions

def save_demo_data():
    """Save all demo data to JSON files"""
    demo_data = {
        "transactions": generate_demo_bank_transactions(),
        "invoices": generate_demo_invoice_data(), 
        "statistics": generate_reconciliation_statistics(),
        "activity_log": generate_activity_log(),
        "exceptions": generate_exceptions_data()
    }
    
    with open('demo_reconciliation_data.json', 'w') as f:
        json.dump(demo_data, f, indent=2)
    
    print("Demo reconciliation data generated successfully!")
    print(f"Generated {len(demo_data['transactions'])} transactions")
    print(f"Generated {len(demo_data['invoices'])} invoices") 
    print(f"Generated {len(demo_data['activity_log'])} activity entries")
    print(f"Generated {len(demo_data['exceptions'])} exceptions")
    
    return demo_data

if __name__ == "__main__":
    demo_data = save_demo_data()