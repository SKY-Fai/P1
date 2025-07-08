#!/usr/bin/env python3
"""
F-AI Accountant One-Click Setup
Automated installation and configuration script
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import json
from pathlib import Path
import time

class FAIAccountantInstaller:
    """One-click installer for F-AI Accountant"""
    
    def __init__(self):
        self.system = platform.system()
        self.python_cmd = self._get_python_command()
        self.pip_cmd = self._get_pip_command()
        
    def _get_python_command(self):
        """Get the correct Python command for the system"""
        if self.system == "Windows":
            # Try different Python commands on Windows
            for cmd in ["python", "py", "python3"]:
                try:
                    result = subprocess.run([cmd, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return cmd
                except:
                    continue
        else:
            return "python3"
        return "python"
    
    def _get_pip_command(self):
        """Get the correct pip command for the system"""
        if self.system == "Windows":
            for cmd in ["pip", "py -m pip", "python -m pip"]:
                try:
                    result = subprocess.run(cmd.split() + ["--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return cmd
                except:
                    continue
        else:
            return f"{self.python_cmd} -m pip"
        return "pip"
    
    def print_banner(self):
        """Print installation banner"""
        print("=" * 60)
        print("🚀 F-AI ACCOUNTANT ONE-CLICK INSTALLER")
        print("=" * 60)
        print("Enterprise Accounting SaaS Platform v2.0.0")
        print("Automated Setup and Configuration")
        print("=" * 60)
        print()
    
    def check_python(self):
        """Check Python installation"""
        print("📋 Checking Python installation...")
        try:
            result = subprocess.run([self.python_cmd, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ {version} found")
                
                # Check if version is 3.8+
                version_parts = version.split()[1].split('.')
                major, minor = int(version_parts[0]), int(version_parts[1])
                if major >= 3 and minor >= 8:
                    return True
                else:
                    print(f"❌ Python 3.8+ required, found {version}")
                    return False
            else:
                print("❌ Python not found")
                return False
        except Exception as e:
            print(f"❌ Error checking Python: {e}")
            return False
    
    def install_dependencies(self):
        """Install required dependencies"""
        print("📦 Installing dependencies...")
        
        # Create requirements.txt if it doesn't exist
        requirements = [
            "flask>=2.3.0",
            "flask-sqlalchemy>=3.0.0",
            "flask-login>=0.6.0",
            "werkzeug>=2.3.0",
            "gunicorn>=21.0.0",
            "pandas>=1.5.0",
            "openpyxl>=3.1.0",
            "reportlab>=4.0.0",
            "psycopg2-binary>=2.9.0",
            "email-validator>=2.0.0",
            "flask-dance>=7.0.0",
            "pyjwt>=2.8.0",
            "oauthlib>=3.2.0",
            "numpy>=1.24.0"
        ]
        
        # Use package_requirements.txt if available, otherwise create requirements.txt
        req_file = "requirements.txt"
        if os.path.exists("package_requirements.txt"):
            # Copy package requirements to requirements.txt
            with open("package_requirements.txt", "r") as f:
                req_content = f.read()
            with open("requirements.txt", "w") as f:
                f.write(req_content)
        elif not os.path.exists("requirements.txt"):
            with open("requirements.txt", "w") as f:
                f.write("\n".join(requirements))
        
        try:
            print("   Installing packages...")
            cmd = f"{self.pip_cmd} install -r requirements.txt --quiet"
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Dependency installation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def setup_database(self):
        """Setup database"""
        print("🗄️  Setting up database...")
        try:
            # Create database directory
            os.makedirs("database", exist_ok=True)
            
            # Run database setup
            cmd = f"{self.python_cmd} database/database_manager.py setup"
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Database setup completed")
                return True
            else:
                print(f"❌ Database setup failed: {result.stderr}")
                # Try alternative setup
                return self._alternative_database_setup()
                
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            return self._alternative_database_setup()
    
    def _alternative_database_setup(self):
        """Alternative database setup if main setup fails"""
        print("🔄 Trying alternative database setup...")
        try:
            # Create basic database setup
            import sqlite3
            db_path = "database/fai_accountant.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create basic users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default admin user
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, email, password_hash, role)
                VALUES ('admin', 'admin@fai-accountant.com', 'pbkdf2:sha256:260000$test', 'admin')
            ''')
            
            conn.commit()
            conn.close()
            
            print("✅ Alternative database setup completed")
            return True
            
        except Exception as e:
            print(f"❌ Alternative database setup failed: {e}")
            return False
    
    def create_startup_scripts(self):
        """Create startup scripts"""
        print("📝 Creating startup scripts...")
        
        # Windows batch file
        batch_content = f'''@echo off
title F-AI Accountant Enterprise Server
color 0A

echo.
echo ========================================
echo  F-AI ACCOUNTANT ENTERPRISE v2.0.0
echo ========================================
echo  Complete Enterprise Accounting SaaS
echo ========================================
echo.

echo [INFO] Starting F-AI Accountant Server...
echo.
echo [ACCESS] Application URL: http://localhost:5000
echo [LOGIN]  Username: admin
echo [LOGIN]  Password: test
echo.
echo [STATUS] Server is starting... Please wait
echo [INFO]   Press Ctrl+C to stop the server
echo.

{self.python_cmd} main.py

echo.
echo [INFO] Server stopped
pause
'''
        
        with open("START_F-AI_ACCOUNTANT.bat", "w") as f:
            f.write(batch_content)
        
        # Unix shell script
        shell_content = f'''#!/bin/bash
echo "========================================"
echo " F-AI ACCOUNTANT ENTERPRISE v2.0.0"
echo "========================================"
echo " Complete Enterprise Accounting SaaS"
echo "========================================"
echo ""
echo "[ACCESS] Application URL: http://localhost:5000"
echo "[LOGIN]  Username: admin"
echo "[LOGIN]  Password: test"
echo ""
echo "[STATUS] Starting server..."
echo ""

{self.python_cmd} main.py
'''
        
        with open("start_f_ai_accountant.sh", "w") as f:
            f.write(shell_content)
        
        # Make shell script executable on Unix systems
        if self.system != "Windows":
            os.chmod("start_f_ai_accountant.sh", 0o755)
        
        print("✅ Startup scripts created")
        return True
    
    def create_desktop_shortcut(self):
        """Create desktop shortcut (Windows only)"""
        if self.system != "Windows":
            return True
            
        print("🔗 Creating desktop shortcut...")
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "F-AI Accountant.lnk")
            target = os.path.join(os.getcwd(), "START_F-AI_ACCOUNTANT.bat")
            wDir = os.getcwd()
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = wDir
            shortcut.IconLocation = target
            shortcut.save()
            
            print("✅ Desktop shortcut created")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not create desktop shortcut: {e}")
            return True  # Not critical
    
    def test_installation(self):
        """Test the installation"""
        print("🧪 Testing installation...")
        try:
            # Test import of main modules
            cmd = f"{self.python_cmd} -c \"import flask, app; print('Installation test passed')\""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and "Installation test passed" in result.stdout:
                print("✅ Installation test passed")
                return True
            else:
                print(f"❌ Installation test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing installation: {e}")
            return False
    
    def print_completion_message(self):
        """Print completion message"""
        print()
        print("=" * 60)
        print("🎉 F-AI ACCOUNTANT INSTALLATION COMPLETE!")
        print("=" * 60)
        print()
        print("🚀 Quick Start:")
        if self.system == "Windows":
            print("   Double-click: START_F-AI_ACCOUNTANT.bat")
            print("   Or use desktop shortcut: F-AI Accountant")
        else:
            print("   Run: ./start_f_ai_accountant.sh")
        print()
        print("🌐 Access:")
        print("   URL: http://localhost:5000")
        print("   Username: admin")
        print("   Password: test")
        print()
        print("📁 Package Contents:")
        print("   ✅ AI Accounting Module")
        print("   ✅ Manual Journal Entry System")
        print("   ✅ Bank Reconciliation Engine")
        print("   ✅ Template Management System")
        print("   ✅ Report Generation Engine")
        print("   ✅ User Management & Permissions")
        print("   ✅ Complete Documentation")
        print()
        print("🎯 Ready to use! Start with the AI Accounting dashboard.")
        print("=" * 60)
    
    def run_installation(self):
        """Run the complete installation process"""
        self.print_banner()
        
        steps = [
            ("Python Check", self.check_python),
            ("Dependencies", self.install_dependencies),
            ("Database Setup", self.setup_database),
            ("Startup Scripts", self.create_startup_scripts),
            ("Desktop Shortcut", self.create_desktop_shortcut),
            ("Installation Test", self.test_installation)
        ]
        
        for step_name, step_func in steps:
            print(f"🔄 {step_name}...")
            if not step_func():
                print(f"❌ {step_name} failed. Installation cannot continue.")
                return False
            time.sleep(0.5)  # Brief pause for user feedback
        
        self.print_completion_message()
        return True

def main():
    """Main installation function"""
    installer = FAIAccountantInstaller()
    
    try:
        success = installer.run_installation()
        if success:
            print("\n🎉 Installation completed successfully!")
            
            # Ask user if they want to start the application
            if installer.system == "Windows":
                response = input("\nWould you like to start F-AI Accountant now? (y/n): ")
                if response.lower() in ['y', 'yes']:
                    subprocess.Popen(["START_F-AI_ACCOUNTANT.bat"], shell=True)
            
            return 0
        else:
            print("\n❌ Installation failed. Please check the errors above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error during installation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())