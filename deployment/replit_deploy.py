
#!/usr/bin/env python3
"""
F-AI Accountant - Replit Deployment Configuration
Production deployment script for Replit with GCP integration
"""

import os
import json
import subprocess
import sys
from pathlib import Path

class ReplitDeployment:
    """Replit deployment configuration and management"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.deployment_config = {
            "name": "F-AI Accountant Enterprise",
            "version": "2.0.0",
            "environment": "production"
        }
    
    def configure_environment(self):
        """Configure environment variables for production"""
        env_vars = {
            # Flask configuration
            "FLASK_ENV": "production",
            "FLASK_APP": "main.py",
            "SECRET_KEY": "fai-accountant-production-secret-2024",
            
            # Database configuration
            "DATABASE_URL": "postgresql://fai_user:fai_password@localhost:5432/fai_accountant",
            
            # GCP Object Storage
            "GCS_BUCKET_NAME": "fai-accountant-storage",
            "GCS_PROJECT_ID": "replit-gcs-project",
            "GCS_REGION": "us-central1",
            
            # Security and compliance
            "AUDIT_LOGGING_ENABLED": "true",
            "RETENTION_DAYS": "2555",
            "ENCRYPTION_ENABLED": "true",
            
            # Performance
            "WEB_CONCURRENCY": "4",
            "MAX_WORKERS": "4",
            "TIMEOUT": "300"
        }
        
        print("🔧 Configuring environment variables...")
        for key, value in env_vars.items():
            os.environ[key] = value
            print(f"   {key} = {value}")
        
        return True
    
    def setup_directories(self):
        """Create necessary directories for production"""
        directories = [
            "uploads",
            "reports", 
            "logs",
            "temp",
            "database/backups",
            "static/uploads",
            "templates_download"
        ]
        
        print("📁 Creating production directories...")
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✓ {directory}")
        
        return True
    
    def install_dependencies(self):
        """Install production dependencies"""
        print("📦 Installing production dependencies...")
        
        try:
            # Install Python packages
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "package_requirements.txt"
            ], check=True, cwd=self.project_root)
            
            # Install additional production packages
            production_packages = [
                "gunicorn>=21.0.0",
                "psycopg2-binary>=2.9.0",
                "redis>=4.5.0"
            ]
            
            subprocess.run([
                sys.executable, "-m", "pip", "install"
            ] + production_packages, check=True)
            
            print("   ✓ Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Dependency installation failed: {e}")
            return False
    
    def setup_database(self):
        """Setup production database"""
        print("🗄️ Setting up production database...")
        
        try:
            subprocess.run([
                sys.executable, "database/production_setup.py", "production"
            ], check=True, cwd=self.project_root)
            
            print("   ✓ Database setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Database setup failed: {e}")
            return False
    
    def configure_gcp_storage(self):
        """Configure GCP Object Storage integration"""
        print("☁️  Configuring GCP Object Storage...")
        
        try:
            from services.gcp_storage_service import GCPStorageService
            
            storage_service = GCPStorageService()
            storage_service.configure_bucket_policies()
            
            print("   ✓ GCP Storage configured successfully")
            return True
            
        except Exception as e:
            print(f"   ❌ GCP Storage configuration failed: {e}")
            return False
    
    def create_health_check(self):
        """Create health check endpoint"""
        print("🏥 Setting up health monitoring...")
        
        health_check_content = '''#!/usr/bin/env python3
import requests
import sys
import time

def health_check():
    """Health check for production monitoring"""
    try:
        response = requests.get("http://0.0.0.0:5000/health", timeout=10)
        if response.status_code == 200:
            print("✓ Application is healthy")
            return 0
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return 1
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(health_check())
'''
        
        health_check_path = self.project_root / "health_check.py"
        with open(health_check_path, "w") as f:
            f.write(health_check_content)
        
        os.chmod(health_check_path, 0o755)
        print("   ✓ Health check configured")
        return True
    
    def create_startup_script(self):
        """Create production startup script"""
        print("🚀 Creating startup script...")
        
        startup_content = '''#!/bin/bash
# F-AI Accountant Production Startup Script

echo "🚀 Starting F-AI Accountant Enterprise v2.0.0"
echo "================================================"

# Set environment
export FLASK_ENV=production
export PYTHONPATH=$PWD

# Database setup
echo "🗄️ Setting up database..."
python database/production_setup.py production

# Start application with Gunicorn
echo "🌐 Starting production server..."
echo "   Access URL: https://your-repl-name.replit.app"
echo "   Health Check: https://your-repl-name.replit.app/health"

exec python main.py
'''
        
        startup_path = self.project_root / "start_production.sh"
        with open(startup_path, "w") as f:
            f.write(startup_content)
        
        os.chmod(startup_path, 0o755)
        print("   ✓ Startup script created")
        return True
    
    def validate_deployment(self):
        """Validate deployment configuration"""
        print("✅ Validating deployment...")
        
        checks = [
            ("Flask app", self._check_flask_app),
            ("Database connection", self._check_database),
            ("GCP Storage", self._check_gcp_storage),
            ("Required files", self._check_required_files)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if check_func():
                    print(f"   ✓ {check_name}")
                else:
                    print(f"   ❌ {check_name}")
                    all_passed = False
            except Exception as e:
                print(f"   ❌ {check_name}: {e}")
                all_passed = False
        
        return all_passed
    
    def _check_flask_app(self):
        """Check Flask application"""
        try:
            from main import app
            return app is not None
        except:
            return False
    
    def _check_database(self):
        """Check database connectivity"""
        try:
            from app import db
            db.session.execute('SELECT 1')
            return True
        except:
            return False
    
    def _check_gcp_storage(self):
        """Check GCP storage service"""
        try:
            from services.gcp_storage_service import GCPStorageService
            storage = GCPStorageService()
            return storage.client is not None
        except:
            return False
    
    def _check_required_files(self):
        """Check required files exist"""
        required_files = [
            "main.py",
            "config.py", 
            "database/production_setup.py",
            "services/gcp_storage_service.py"
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                return False
        
        return True
    
    def deploy(self):
        """Run complete deployment process"""
        print("🚀 F-AI ACCOUNTANT PRODUCTION DEPLOYMENT")
        print("=" * 50)
        
        steps = [
            ("Environment Configuration", self.configure_environment),
            ("Directory Setup", self.setup_directories),
            ("Dependencies Installation", self.install_dependencies),
            ("Database Setup", self.setup_database),
            ("GCP Storage Configuration", self.configure_gcp_storage),
            ("Health Check Setup", self.create_health_check),
            ("Startup Script Creation", self.create_startup_script),
            ("Deployment Validation", self.validate_deployment)
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"❌ {step_name} failed. Deployment aborted.")
                return False
        
        print("\n" + "=" * 50)
        print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("\n📋 Next Steps:")
        print("1. Configure secrets in Replit Secrets tab")
        print("2. Set up custom domain (optional)")
        print("3. Configure monitoring and alerts")
        print("4. Run health checks")
        print("\n🌐 Access your application:")
        print("   https://your-repl-name.replit.app")
        print("   Health: https://your-repl-name.replit.app/health")
        
        return True

def main():
    """Main deployment function"""
    deployment = ReplitDeployment()
    
    try:
        success = deployment.deploy()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Deployment cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
