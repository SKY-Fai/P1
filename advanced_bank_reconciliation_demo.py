"""
Advanced Bank Reconciliation System Demo
Shows the complete integration with automatic invoice mapping and professional logic
"""

from services.advanced_bank_reconciliation_engine import AdvancedBankReconciliationEngine
from datetime import datetime
import json
import pandas as pd

def run_advanced_reconciliation_demo():
    """Demonstrate the advanced bank reconciliation system"""
    
    print("🚀 ADVANCED BANK RECONCILIATION SYSTEM DEMO")
    print("=" * 60)
    
    # Initialize the engine
    engine = AdvancedBankReconciliationEngine()
    
    # Sample bank statement data
    bank_data = [
        {
            'date': '2024-01-15',
            'description': 'NEFT CR ABC TECHNOLOGIES INV2024001 SOFTWARE PAYMENT',
            'amount': 59000,  # Including GST
            'reference': 'NEFT789123',
            'balance': 159000
        },
        {
            'date': '2024-01-18',
            'description': 'NEFT CR DIGITAL SOLUTIONS INV2024002 WEBSITE DEV',
            'amount': 88500,  # Including GST  
            'reference': 'NEFT789124',
            'balance': 247500
        },
        {
            'date': '2024-01-10',
            'description': 'UPI DR OFFICE SUPPLIES BILL001 FURNITURE',
            'amount': -17700,  # Including GST
            'reference': 'UPI456789',
            'balance': 100000
        },
        {
            'date': '2024-01-12',
            'description': 'NEFT DR SOFTWARE LICENSES BILL002 ANNUAL LICENSE',
            'amount': -29500,  # Including GST
            'reference': 'NEFT456123',
            'balance': 70500
        },
        {
            'date': '2024-01-20',
            'description': 'SALARY PAYMENT TO EMPLOYEES',
            'amount': -150000,
            'reference': 'SAL202401',
            'balance': 97500
        }
    ]
    
    # Sample invoice data for mapping
    invoice_data = [
        {
            'invoice_number': 'INV-2024-001',
            'party_name': 'ABC Technologies Pvt Ltd',
            'amount': 50000,
            'date': '2024-01-15',
            'description': 'Software development services',
            'gst_number': '27ABCTY1234F1Z5',
            'transaction_type': 'sales'
        },
        {
            'invoice_number': 'INV-2024-002',
            'party_name': 'Digital Solutions Ltd',
            'amount': 75000,
            'date': '2024-01-18',
            'description': 'Website development project',
            'gst_number': '19DIGSOL5678E2A3',
            'transaction_type': 'sales'
        },
        {
            'invoice_number': 'BILL-001',
            'party_name': 'Office Supplies Co',
            'amount': 15000,
            'date': '2024-01-10',
            'description': 'Office furniture and equipment',
            'gst_number': '07OFFSUP3456D7E8',
            'transaction_type': 'purchase'
        },
        {
            'invoice_number': 'BILL-002',
            'party_name': 'Software Licenses Ltd',
            'amount': 25000,
            'date': '2024-01-12',
            'description': 'Annual software licenses',
            'gst_number': '12SOFTLIC7890F1G2',
            'transaction_type': 'purchase'
        }
    ]
    
    # Load data
    print("\n📊 LOADING DATA")
    print("-" * 20)
    
    bank_loaded = engine.load_bank_statement(bank_data)
    invoice_loaded = engine.load_invoice_data(invoice_data)
    
    print(f"✅ Bank transactions loaded: {len(engine.bank_transactions)}")
    print(f"✅ Invoices loaded: {len(engine.invoices)}")
    
    if not bank_loaded or not invoice_loaded:
        print("❌ Failed to load data")
        return
    
    # Perform automatic mapping
    print("\n🔄 PERFORMING AUTOMATIC MAPPING")
    print("-" * 35)
    
    mapping_results = engine.perform_automatic_mapping()
    
    print(f"✅ Perfect matches: {len(mapping_results['perfect_matches'])}")
    print(f"🔸 High confidence matches: {len(mapping_results['high_confidence_matches'])}")
    print(f"🔶 Moderate matches: {len(mapping_results['moderate_matches'])}")
    print(f"🔻 Low confidence matches: {len(mapping_results['low_confidence_matches'])}")
    print(f"⚠️  Unmapped transactions: {len(mapping_results['unmapped_transactions'])}")
    
    # Show detailed matching results
    print("\n📋 DETAILED MATCHING RESULTS")
    print("-" * 30)
    
    for category, matches in mapping_results.items():
        if matches and category != 'unmapped_transactions':
            print(f"\n{category.upper().replace('_', ' ')}:")
            for match in matches:
                bank_tx = next((bt for bt in engine.bank_transactions 
                              if bt.transaction_id == match.bank_transaction_id), None)
                invoice = next((inv for inv in engine.invoices 
                              if inv.invoice_id == match.invoice_id), None)
                
                if bank_tx and invoice:
                    print(f"  • {bank_tx.description[:50]}...")
                    print(f"    ↔ {invoice.invoice_number} - {invoice.party_name}")
                    print(f"    Confidence: {match.confidence_score:.1%}")
                    print(f"    Factors: Amount({match.mapping_factors.get('amount_match', 0):.1%}), "
                          f"Date({match.mapping_factors.get('date_proximity', 0):.1%}), "
                          f"Reference({match.mapping_factors.get('reference_match', 0):.1%})")
    
    # Show unmapped transactions
    if mapping_results['unmapped_transactions']:
        print(f"\n❌ UNMAPPED TRANSACTIONS:")
        for match in mapping_results['unmapped_transactions']:
            bank_tx = next((bt for bt in engine.bank_transactions 
                          if bt.transaction_id == match.bank_transaction_id), None)
            if bank_tx:
                print(f"  • {bank_tx.description}")
                print(f"    Amount: ₹{bank_tx.amount:,.2f}")
                print(f"    Suggested Account: {match.suggested_account}")
                print(f"    Manual mapping required")
    
    # Generate reconciliation report
    print("\n📊 RECONCILIATION REPORT")
    print("-" * 25)
    
    report = engine.generate_reconciliation_report()
    summary = report['reconciliation_summary']
    
    print(f"Total Transactions: {summary['total_transactions']}")
    print(f"Matched Transactions: {summary['matched_transactions']}")
    print(f"Unmapped Transactions: {summary['unmapped_transactions']}")
    print(f"Matching Rate: {summary['matching_percentage']:.1f}%")
    print(f"Total Credits: ₹{summary['total_credits']:,.2f}")
    print(f"Total Debits: ₹{summary['total_debits']:,.2f}")
    print(f"Matched Amount: ₹{summary['matched_amount']:,.2f}")
    print(f"Unmapped Amount: ₹{summary['unmapped_amount']:,.2f}")
    
    # Show confidence breakdown
    print(f"\n🎯 CONFIDENCE BREAKDOWN:")
    confidence = report['confidence_breakdown']
    for level, count in confidence.items():
        print(f"  {level.replace('_', ' ').title()}: {count}")
    
    # Export results
    print("\n💾 EXPORTING RESULTS")
    print("-" * 20)
    
    export_success = engine.export_reconciliation_results("demo_reconciliation_results.xlsx")
    if export_success:
        print("✅ Results exported to demo_reconciliation_results.xlsx")
    else:
        print("❌ Export failed")
    
    # Show integration capabilities
    print("\n🔗 INTEGRATION CAPABILITIES")
    print("-" * 28)
    print("✅ Automatic invoice mapping with professional logic")
    print("✅ Multi-factor confidence scoring (amount, date, reference, party, description)")
    print("✅ GST-aware amount matching")
    print("✅ Intelligent pattern recognition")
    print("✅ Manual mapping interface for unmapped transactions")
    print("✅ Professional account suggestions")
    print("✅ Comprehensive audit trail")
    print("✅ Excel export capabilities")
    print("✅ Real-time confidence analysis")
    print("✅ Management review flagging")
    print("✅ Transaction ignore functionality")
    
    print("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
    print("   Advanced Bank Reconciliation System is fully operational")
    print("   and integrated with the AI Accounting module.")
    
    return report

if __name__ == "__main__":
    try:
        demo_report = run_advanced_reconciliation_demo()
        
        # Save demo report
        with open('demo_reconciliation_report.json', 'w') as f:
            json.dump(demo_report, f, indent=2, default=str)
        print("\n📄 Demo report saved to demo_reconciliation_report.json")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()