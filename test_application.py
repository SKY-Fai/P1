
#!/usr/bin/env python3
"""
F-AI Accountant - Application Test Suite
Tests all major components and endpoints
"""

import os
import sys
import requests
import time
import json
from datetime import datetime

def test_application():
    """Test the F-AI Accountant application"""
    print("🧪 F-AI ACCOUNTANT - APPLICATION TEST")
    print("=" * 50)
    
    # Test application startup
    print("\n1. Testing Application Startup...")
    try:
        from main import app
        print("✓ Flask application imported successfully")
        
        with app.app_context():
            from app import db
            db.session.execute('SELECT 1')
            print("✓ Database connection verified")
            
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        return False
    
    # Test health endpoint (if running)
    print("\n2. Testing Health Endpoint...")
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ Health check passed: {health_data['status']}")
        else:
            print(f"⚠ Health check returned: {response.status_code}")
    except Exception as e:
        print(f"⚠ Health endpoint not accessible (app may not be running): {e}")
    
    # Test core modules
    print("\n3. Testing Core Modules...")
    modules_to_test = [
        ("Automated Accounting Engine", "services.automated_accounting_engine"),
        ("Bank Reconciliation Engine", "services.bank_reconciliation_engine"),
        ("Manual Journal Service", "services.manual_journal_service"),
        ("File Processor", "services.file_processor"),
        ("Report Generator", "services.report_generator"),
        ("GCP Storage Service", "services.gcp_storage_service")
    ]
    
    for module_name, module_path in modules_to_test:
        try:
            __import__(module_path)
            print(f"✓ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
    
    # Test templates
    print("\n4. Testing Templates...")
    template_files = [
        "templates/base.html",
        "templates/dashboard.html",
        "templates/automated_accounting_dashboard.html",
        "templates/bank_reconciliation.html",
        "templates/financial_reports.html"
    ]
    
    for template in template_files:
        if os.path.exists(template):
            print(f"✓ {template}")
        else:
            print(f"❌ {template} - Missing")
    
    # Test static files
    print("\n5. Testing Static Files...")
    static_files = [
        "static/css/unified-styles.css",
        "static/js/app.js",
        "static/js/navigation.js"
    ]
    
    for static_file in static_files:
        if os.path.exists(static_file):
            print(f"✓ {static_file}")
        else:
            print(f"❌ {static_file} - Missing")
    
    # Test database tables
    print("\n6. Testing Database Schema...")
    try:
        from main import app
        with app.app_context():
            from app import db
            from models import User, UploadRecord, JournalEntry
            
            # Test table creation
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Test basic operations
            user_count = User.query.count()
            print(f"✓ User table accessible (count: {user_count})")
            
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 APPLICATION TEST COMPLETED")
    print("=" * 50)
    
    print("\n📋 NEXT STEPS:")
    print("1. Click the Run button to start the server")
    print("2. Access your application at the provided URL")
    print("3. Login with: admin / test")
    print("4. Test core features:")
    print("   - File Upload & Processing")
    print("   - Automated Accounting")
    print("   - Bank Reconciliation")
    print("   - Report Generation")
    
    return True

if __name__ == "__main__":
    test_application()
