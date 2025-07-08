"""
VALIDATION DASHBOARD
===================

Comprehensive validation and monitoring dashboard for AI Accounting, Manual Journal,
and Bank Reconciliation modules with complete audit trail and downloads management.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

@dataclass
class ValidationEvent:
    """Represents a validation event for audit trail"""
    event_id: str
    timestamp: str
    module: str
    event_type: str
    description: str
    user_id: str
    ip_address: str
    parameters: Dict[str, Any]
    status: str
    duration_ms: float
    error_message: Optional[str] = None

@dataclass
class DownloadEvent:
    """Represents a download event"""
    download_id: str
    timestamp: str
    file_type: str
    file_category: str
    file_name: str
    file_path: str
    user_id: str
    ip_address: str
    file_size: int
    status: str

@dataclass
class UploadEvent:
    """Represents an upload event"""
    upload_id: str
    timestamp: str
    file_type: str
    original_name: str
    stored_path: str
    user_id: str
    ip_address: str
    file_size: int
    processing_status: str
    validation_results: Dict[str, Any]

class ValidationDashboard:
    """
    Comprehensive validation dashboard with audit trail and file management
    """
    
    def __init__(self):
        self.base_dir = Path(".")
        self.setup_directories()
        self.setup_database()
        self.setup_logging()
        
        # Module validation configs
        self.module_configs = {
            'ai_accounting': {
                'name': 'AI Accounting Engine',
                'validation_points': ['template_processing', 'journal_generation', 'double_entry_validation'],
                'critical_thresholds': {'processing_time': 5000, 'error_rate': 0.05}
            },
            'manual_journal': {
                'name': 'Manual Journal Service',
                'validation_points': ['entry_validation', 'balance_verification', 'rules_compliance'],
                'critical_thresholds': {'processing_time': 2000, 'error_rate': 0.02}
            },
            'bank_reconciliation': {
                'name': 'Bank Reconciliation Engine',
                'validation_points': ['transaction_matching', 'confidence_scoring', 'manual_mapping'],
                'critical_thresholds': {'processing_time': 8000, 'error_rate': 0.10}
            }
        }
    
    def setup_directories(self):
        """Setup directory structure for dashboard"""
        self.directories = {
            'templates': self.base_dir / 'templates_library',
            'reports': self.base_dir / 'reports_output',
            'uploads': self.base_dir / 'uploads_input',
            'logs': self.base_dir / 'validation_logs',
            'downloads': self.base_dir / 'downloads_archive'
        }
        
        for dir_path in self.directories.values():
            dir_path.mkdir(exist_ok=True)
            
        # Create subdirectories for templates
        template_categories = [
            'accounting_templates', 'invoice_templates', 'journal_templates',
            'reconciliation_templates', 'reporting_templates'
        ]
        for category in template_categories:
            (self.directories['templates'] / category).mkdir(exist_ok=True)
        
        # Create subdirectories for reports
        report_categories = [
            'financial_reports', 'reconciliation_reports', 'validation_reports',
            'audit_reports', 'compliance_reports'
        ]
        for category in report_categories:
            (self.directories['reports'] / category).mkdir(exist_ok=True)
    
    def setup_database(self):
        """Setup SQLite database for audit trail"""
        self.db_path = self.base_dir / 'validation_dashboard.db'
        
        with sqlite3.connect(self.db_path) as conn:
            # Validation events table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS validation_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    module TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    ip_address TEXT,
                    parameters TEXT,
                    status TEXT NOT NULL,
                    duration_ms REAL,
                    error_message TEXT
                )
            ''')
            
            # Download events table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS download_events (
                    download_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_category TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    ip_address TEXT,
                    file_size INTEGER,
                    status TEXT NOT NULL
                )
            ''')
            
            # Upload events table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS upload_events (
                    upload_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    ip_address TEXT,
                    file_size INTEGER,
                    processing_status TEXT NOT NULL,
                    validation_results TEXT
                )
            ''')
            
            # Module health metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS module_health (
                    metric_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    module TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    status TEXT NOT NULL,
                    threshold_breached BOOLEAN
                )
            ''')
            
            conn.commit()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.directories['logs'] / f'validation_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ValidationDashboard')
    
    def log_validation_event(self, module: str, event_type: str, description: str,
                           user_id: str, ip_address: str = None, parameters: Dict = None,
                           status: str = 'SUCCESS', duration_ms: float = 0,
                           error_message: str = None) -> str:
        """Log a validation event to audit trail"""
        
        event_id = f"VAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{module[:3].upper()}_{hash(description) % 10000:04d}"
        
        event = ValidationEvent(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            module=module,
            event_type=event_type,
            description=description,
            user_id=user_id,
            ip_address=ip_address or 'unknown',
            parameters=parameters or {},
            status=status,
            duration_ms=duration_ms,
            error_message=error_message
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO validation_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id, event.timestamp, event.module, event.event_type,
                event.description, event.user_id, event.ip_address,
                json.dumps(event.parameters), event.status, event.duration_ms,
                event.error_message
            ))
            conn.commit()
        
        # Log to file
        self.logger.info(f"VALIDATION_EVENT: {event.module} - {event.event_type} - {event.status}")
        
        return event_id
    
    def log_download_event(self, file_type: str, file_category: str, file_name: str,
                          file_path: str, user_id: str, ip_address: str = None,
                          file_size: int = 0, status: str = 'SUCCESS') -> str:
        """Log a download event"""
        
        download_id = f"DL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(file_name) % 10000:04d}"
        
        event = DownloadEvent(
            download_id=download_id,
            timestamp=datetime.now().isoformat(),
            file_type=file_type,
            file_category=file_category,
            file_name=file_name,
            file_path=file_path,
            user_id=user_id,
            ip_address=ip_address or 'unknown',
            file_size=file_size,
            status=status
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO download_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.download_id, event.timestamp, event.file_type, event.file_category,
                event.file_name, event.file_path, event.user_id, event.ip_address,
                event.file_size, event.status
            ))
            conn.commit()
        
        self.logger.info(f"DOWNLOAD_EVENT: {file_name} - {file_category} - {status}")
        return download_id
    
    def log_upload_event(self, file_type: str, original_name: str, stored_path: str,
                        user_id: str, ip_address: str = None, file_size: int = 0,
                        processing_status: str = 'PENDING',
                        validation_results: Dict = None) -> str:
        """Log an upload event"""
        
        upload_id = f"UP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(original_name) % 10000:04d}"
        
        event = UploadEvent(
            upload_id=upload_id,
            timestamp=datetime.now().isoformat(),
            file_type=file_type,
            original_name=original_name,
            stored_path=stored_path,
            user_id=user_id,
            ip_address=ip_address or 'unknown',
            file_size=file_size,
            processing_status=processing_status,
            validation_results=validation_results or {}
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO upload_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.upload_id, event.timestamp, event.file_type, event.original_name,
                event.stored_path, event.user_id, event.ip_address, event.file_size,
                event.processing_status, json.dumps(event.validation_results)
            ))
            conn.commit()
        
        self.logger.info(f"UPLOAD_EVENT: {original_name} - {processing_status}")
        return upload_id
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Recent validation events (last 24 hours)
            recent_events = conn.execute('''
                SELECT module, status, COUNT(*) as count
                FROM validation_events
                WHERE timestamp > datetime('now', '-1 day')
                GROUP BY module, status
            ''').fetchall()
            
            # Download statistics
            download_stats = conn.execute('''
                SELECT file_category, COUNT(*) as count, SUM(file_size) as total_size
                FROM download_events
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY file_category
            ''').fetchall()
            
            # Upload statistics
            upload_stats = conn.execute('''
                SELECT processing_status, COUNT(*) as count
                FROM upload_events
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY processing_status
            ''').fetchall()
            
            # Module health overview
            module_health = {}
            for module, config in self.module_configs.items():
                module_events = conn.execute('''
                    SELECT status, COUNT(*) as count
                    FROM validation_events
                    WHERE module = ? AND timestamp > datetime('now', '-1 hour')
                    GROUP BY status
                ''', (module,)).fetchall()
                
                total_events = sum(count for _, count in module_events)
                error_events = sum(count for status, count in module_events if status == 'ERROR')
                error_rate = error_events / total_events if total_events > 0 else 0
                
                module_health[module] = {
                    'status': 'HEALTHY' if error_rate < config['critical_thresholds']['error_rate'] else 'WARNING',
                    'error_rate': error_rate,
                    'total_events': total_events,
                    'last_check': datetime.now().isoformat()
                }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'recent_validation_events': {
                'events': recent_events,
                'summary': {
                    'total': sum(count for _, _, count in recent_events),
                    'errors': sum(count for _, status, count in recent_events if status == 'ERROR')
                }
            },
            'download_statistics': {
                'by_category': download_stats,
                'total_downloads': sum(count for _, count, _ in download_stats),
                'total_size_mb': sum(size for _, _, size in download_stats if size) / (1024 * 1024)
            },
            'upload_statistics': {
                'by_status': upload_stats,
                'total_uploads': sum(count for _, count in upload_stats)
            },
            'module_health': module_health,
            'system_status': self._get_system_status(module_health)
        }
    
    def _get_system_status(self, module_health: Dict) -> str:
        """Determine overall system status"""
        statuses = [health['status'] for health in module_health.values()]
        
        if all(status == 'HEALTHY' for status in statuses):
            return 'ALL_SYSTEMS_OPERATIONAL'
        elif any(status == 'ERROR' for status in statuses):
            return 'CRITICAL_ISSUES_DETECTED'
        else:
            return 'WARNINGS_DETECTED'
    
    def get_templates_library(self) -> Dict[str, List[Dict]]:
        """Get organized templates library"""
        templates_library = {}
        
        for category_dir in self.directories['templates'].iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                templates_library[category_name] = []
                
                for template_file in category_dir.glob('*'):
                    if template_file.is_file():
                        file_stats = template_file.stat()
                        templates_library[category_name].append({
                            'name': template_file.name,
                            'path': str(template_file),
                            'size': file_stats.st_size,
                            'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                            'type': template_file.suffix.lower()
                        })
        
        return templates_library
    
    def get_reports_output(self) -> Dict[str, List[Dict]]:
        """Get organized reports output"""
        reports_output = {}
        
        for category_dir in self.directories['reports'].iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                reports_output[category_name] = []
                
                for report_file in category_dir.glob('*'):
                    if report_file.is_file():
                        file_stats = report_file.stat()
                        reports_output[category_name].append({
                            'name': report_file.name,
                            'path': str(report_file),
                            'size': file_stats.st_size,
                            'generated': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                            'type': report_file.suffix.lower(),
                            'category': category_name
                        })
        
        return reports_output
    
    def get_uploads_input(self) -> List[Dict]:
        """Get uploads input with processing status"""
        uploads = []
        
        # Get uploads from database with processing status
        with sqlite3.connect(self.db_path) as conn:
            upload_records = conn.execute('''
                SELECT upload_id, timestamp, file_type, original_name, stored_path,
                       user_id, file_size, processing_status, validation_results
                FROM upload_events
                ORDER BY timestamp DESC
                LIMIT 100
            ''').fetchall()
            
            for record in upload_records:
                upload_id, timestamp, file_type, original_name, stored_path, user_id, file_size, processing_status, validation_results = record
                
                uploads.append({
                    'upload_id': upload_id,
                    'timestamp': timestamp,
                    'file_type': file_type,
                    'original_name': original_name,
                    'stored_path': stored_path,
                    'user_id': user_id,
                    'file_size': file_size,
                    'processing_status': processing_status,
                    'validation_results': json.loads(validation_results) if validation_results else {},
                    'file_exists': Path(stored_path).exists() if stored_path else False
                })
        
        return uploads
    
    def get_audit_trail(self, module: str = None, event_type: str = None,
                       start_date: str = None, end_date: str = None,
                       limit: int = 1000) -> List[Dict]:
        """Get filtered audit trail"""
        
        query = 'SELECT * FROM validation_events WHERE 1=1'
        params = []
        
        if module:
            query += ' AND module = ?'
            params.append(module)
        
        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            columns = [description[0] for description in cursor.description]
            
            audit_records = []
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                if record['parameters']:
                    record['parameters'] = json.loads(record['parameters'])
                audit_records.append(record)
        
        return audit_records
    
    def validate_module_health(self, module: str) -> Dict[str, Any]:
        """Comprehensive module health validation"""
        
        config = self.module_configs.get(module)
        if not config:
            return {'error': f'Unknown module: {module}'}
        
        validation_results = {
            'module': module,
            'timestamp': datetime.now().isoformat(),
            'status': 'HEALTHY',
            'issues': [],
            'metrics': {},
            'recommendations': []
        }
        
        # Check recent error rates
        with sqlite3.connect(self.db_path) as conn:
            recent_events = conn.execute('''
                SELECT status, COUNT(*) as count, AVG(duration_ms) as avg_duration
                FROM validation_events
                WHERE module = ? AND timestamp > datetime('now', '-1 hour')
                GROUP BY status
            ''', (module,)).fetchall()
            
            total_events = sum(count for _, count, _ in recent_events)
            error_events = sum(count for status, count, _ in recent_events if status == 'ERROR')
            avg_duration = sum(duration for _, _, duration in recent_events if duration) / len(recent_events) if recent_events else 0
            
            error_rate = error_events / total_events if total_events > 0 else 0
            
            validation_results['metrics'] = {
                'total_events': total_events,
                'error_events': error_events,
                'error_rate': error_rate,
                'average_duration_ms': avg_duration
            }
            
            # Check against thresholds
            if error_rate > config['critical_thresholds']['error_rate']:
                validation_results['status'] = 'WARNING'
                validation_results['issues'].append(f'Error rate ({error_rate:.2%}) exceeds threshold ({config["critical_thresholds"]["error_rate"]:.2%})')
            
            if avg_duration > config['critical_thresholds']['processing_time']:
                validation_results['status'] = 'WARNING'
                validation_results['issues'].append(f'Average processing time ({avg_duration:.0f}ms) exceeds threshold ({config["critical_thresholds"]["processing_time"]}ms)')
        
        # Generate recommendations
        if validation_results['status'] == 'WARNING':
            validation_results['recommendations'].append('Review recent error logs for patterns')
            validation_results['recommendations'].append('Consider performance optimization')
            if error_rate > 0.1:
                validation_results['recommendations'].append('Investigate critical error causes immediately')
        else:
            validation_results['recommendations'].append('Module operating within normal parameters')
        
        return validation_results
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation and audit report"""
        
        report = {
            'report_id': f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'generated_at': datetime.now().isoformat(),
            'dashboard_metrics': self.get_dashboard_metrics(),
            'module_validations': {},
            'templates_inventory': self.get_templates_library(),
            'reports_inventory': self.get_reports_output(),
            'uploads_status': self.get_uploads_input(),
            'audit_summary': self._generate_audit_summary(),
            'recommendations': []
        }
        
        # Validate each module
        for module in self.module_configs.keys():
            report['module_validations'][module] = self.validate_module_health(module)
        
        # Generate overall recommendations
        overall_status = report['dashboard_metrics']['system_status']
        if overall_status == 'ALL_SYSTEMS_OPERATIONAL':
            report['recommendations'].append('All systems operating normally - continue monitoring')
        elif overall_status == 'WARNINGS_DETECTED':
            report['recommendations'].append('Address warning conditions to prevent escalation')
            report['recommendations'].append('Review module-specific recommendations')
        else:
            report['recommendations'].append('URGENT: Address critical issues immediately')
            report['recommendations'].append('Review error logs and contact technical support if needed')
        
        return report
    
    def _generate_audit_summary(self) -> Dict[str, Any]:
        """Generate audit trail summary"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Events by module in last 24 hours
            module_summary = conn.execute('''
                SELECT module, COUNT(*) as events, 
                       SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as errors
                FROM validation_events
                WHERE timestamp > datetime('now', '-1 day')
                GROUP BY module
            ''').fetchall()
            
            # Top users by activity
            user_activity = conn.execute('''
                SELECT user_id, COUNT(*) as activities
                FROM validation_events
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY user_id
                ORDER BY activities DESC
                LIMIT 10
            ''').fetchall()
            
            # Recent critical events
            critical_events = conn.execute('''
                SELECT event_id, timestamp, module, event_type, description
                FROM validation_events
                WHERE status = 'ERROR' AND timestamp > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
                LIMIT 10
            ''').fetchall()
        
        return {
            'module_summary': [
                {'module': module, 'events': events, 'errors': errors}
                for module, events, errors in module_summary
            ],
            'top_users': [
                {'user_id': user_id, 'activities': activities}
                for user_id, activities in user_activity
            ],
            'critical_events': [
                {
                    'event_id': event_id,
                    'timestamp': timestamp,
                    'module': module,
                    'event_type': event_type,
                    'description': description
                }
                for event_id, timestamp, module, event_type, description in critical_events
            ]
        }

def create_validation_dashboard():
    """Create and initialize validation dashboard"""
    dashboard = ValidationDashboard()
    
    # Log initial setup
    dashboard.log_validation_event(
        module='system',
        event_type='dashboard_initialization',
        description='Validation dashboard initialized successfully',
        user_id='system',
        status='SUCCESS'
    )
    
    return dashboard

if __name__ == "__main__":
    # Initialize dashboard and run basic validation
    dashboard = create_validation_dashboard()
    
    print("Validation Dashboard Initialized")
    print("=" * 50)
    
    # Generate initial report
    report = dashboard.generate_comprehensive_report()
    print(f"Report ID: {report['report_id']}")
    print(f"System Status: {report['dashboard_metrics']['system_status']}")
    print(f"Templates Available: {sum(len(templates) for templates in report['templates_inventory'].values())}")
    print(f"Reports Generated: {sum(len(reports) for reports in report['reports_inventory'].values())}")
    print(f"Recent Uploads: {len(report['uploads_status'])}")