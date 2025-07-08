
#!/usr/bin/env python3
"""
F-AI Accountant - Local Development Setup
Quick setup for local development and testing
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

class LocalDevelopmentSetup:
    """Local development environment setup"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        
    def setup_environment(self):
        """Setup development environment"""
        print("🔧 Setting up development environment...")
        
        # Set development environment variables
        os.environ["FLASK_ENV"] = "development"
        os.environ["FLASK_DEBUG"] = "1"
        os.environ["DATABASE_URL"] = "sqlite:///database/fai_accountant_dev.db"
        
        print("   ✓ Environment configured for development")
        return True
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            "database",
            "uploads", 
            "reports",
            "logs",
            "temp",
            "static/uploads"
        ]
        
        print("📁 Creating development directories...")
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✓ {directory}")
        
        return True
    
    def install_dependencies(self):
        """Install development dependencies"""
        print("📦 Installing development dependencies...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "package_requirements.txt"
            ], check=True)
            
            # Additional development packages
            dev_packages = [
                "flask-debugtoolbar",
                "pytest",
                "pytest-flask"
            ]
            
            subprocess.run([
                sys.executable, "-m", "pip", "install"
            ] + dev_packages, check=True)
            
            print("   ✓ Dependencies installed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install dependencies: {e}")
            return False
    
    def setup_development_database(self):
        """Setup SQLite database for development"""
        print("🗄️ Setting up development database...")
        
        try:
            subprocess.run([
                sys.executable, "database/production_setup.py", "development"
            ], check=True)
            
            print("   ✓ Development database created")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Database setup failed: {e}")
            return False
    
    def create_test_data(self):
        """Create test data for development"""
        print("📊 Creating test data...")
        
        try:
            db_path = "database/fai_accountant_dev.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Additional test users
            test_users = [
                ('testuser', 'test@example.com', 'pbkdf2:sha256:260000$test', 'Test', 'User', 'accountant'),
                ('auditor', 'auditor@example.com', 'pbkdf2:sha256:260000$test', 'Test', 'Auditor', 'auditor'),
                ('manager', 'manager@example.com', 'pbkdf2:sha256:260000$test', 'Test', 'Manager', 'manager')
            ]
            
            for user_data in test_users:
                cursor.execute('''
                    INSERT OR IGNORE INTO users (username, email, password_hash, first_name, last_name, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', user_data)
            
            # Test companies
            cursor.execute('''
                INSERT OR IGNORE INTO companies (name, registration_number, owner_user_id)
                VALUES ('Development Test Co.', 'DEV001', 1)
            ''')
            
            conn.commit()
            conn.close()
            
            print("   ✓ Test data created")
            return True
            
        except Exception as e:
            print(f"   ❌ Test data creation failed: {e}")
            return False
    
    def create_dev_scripts(self):
        """Create development scripts"""
        print("📝 Creating development scripts...")
        
        # Development run script
        run_dev_content = '''#!/usr/bin/env python3
"""Development server runner"""
import os
os.environ["FLASK_ENV"] = "development"
os.environ["FLASK_DEBUG"] = "1"

from main import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
'''
        
        with open("run_dev.py", "w") as f:
            f.write(run_dev_content)
        
        # Test runner script
        test_content = '''#!/usr/bin/env python3
"""Test runner for development"""
import subprocess
import sys

def run_tests():
    """Run all tests"""
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
'''
        
        with open("run_tests.py", "w") as f:
            f.write(test_content)
        
        print("   ✓ Development scripts created")
        return True
    
    def run_setup(self):
        """Run complete development setup"""
        print("🚀 F-AI ACCOUNTANT DEVELOPMENT SETUP")
        print("=" * 40)
        
        steps = [
            ("Environment Setup", self.setup_environment),
            ("Directory Creation", self.create_directories),
            ("Dependencies Installation", self.install_dependencies),
            ("Database Setup", self.setup_development_database),
            ("Test Data Creation", self.create_test_data),
            ("Development Scripts", self.create_dev_scripts)
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"❌ {step_name} failed.")
                return False
        
        print("\n" + "=" * 40)
        print("🎉 DEVELOPMENT SETUP COMPLETED!")
        print("=" * 40)
        print("\n🚀 Quick Start:")
        print("   python run_dev.py")
        print("\n🧪 Run Tests:")
        print("   python run_tests.py")
        print("\n🌐 Access:")
        print("   http://localhost:5000")
        print("   Login: admin / test")
        
        return True

def main():
    """Main setup function"""
    setup = LocalDevelopmentSetup()
    
    try:
        success = setup.run_setup()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Setup cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
