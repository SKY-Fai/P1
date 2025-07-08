
import unittest
import os
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app, db
from models import User, FileStorageMetadata, FileAccessAudit
from services.gcp_storage_service import GCPStorageService

class TestGCPStorageIntegration(unittest.TestCase):
    """Comprehensive test suite for GCP Object Storage integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash='test_hash',
            first_name='Test',
            last_name='User'
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        self.storage_service = GCPStorageService()
        
        # Mock file data
        self.test_file_data = b"test file content for storage testing"
        self.test_filename = "test_document.pdf"
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    @patch('services.gcp_storage_service.Client')
    def test_file_upload_success(self, mock_client):
        """Test successful file upload"""
        # Mock client methods
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        # Test upload
        result = self.storage_service.upload_file(
            file_data=self.test_file_data,
            filename=self.test_filename,
            user_id=self.test_user.id,
            file_category='invoice'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('file_path', result)
        self.assertIn('metadata', result)
        self.assertIn('signed_url', result)
        
        # Verify file path structure
        expected_path_prefix = f"users/{self.test_user.id}/"
        self.assertTrue(result['file_path'].startswith(expected_path_prefix))
    
    @patch('services.gcp_storage_service.Client')
    def test_file_upload_validation_failure(self, mock_client):
        """Test file upload with validation failure"""
        # Test with oversized file
        large_file_data = b"x" * (60 * 1024 * 1024)  # 60MB (over limit)
        
        result = self.storage_service.upload_file(
            file_data=large_file_data,
            filename=self.test_filename,
            user_id=self.test_user.id
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('exceeds maximum', result['error'])
    
    @patch('services.gcp_storage_service.Client')
    def test_file_download_success(self, mock_client):
        """Test successful file download"""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.download_as_bytes.return_value = self.test_file_data
        
        # Create file metadata
        file_path = f"users/{self.test_user.id}/test_file.pdf"
        
        # Mock metadata retrieval
        mock_metadata = {
            'user_id': self.test_user.id,
            'content_type': 'application/pdf',
            'size': len(self.test_file_data)
        }
        mock_client_instance.download_as_text.return_value = json.dumps(mock_metadata)
        
        result = self.storage_service.download_file(file_path, self.test_user.id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data'], self.test_file_data)
        self.assertIn('metadata', result)
    
    @patch('services.gcp_storage_service.Client')
    def test_file_download_access_denied(self, mock_client):
        """Test file download with access denied"""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        # Mock metadata with different user
        mock_metadata = {
            'user_id': 999,  # Different user
            'content_type': 'application/pdf'
        }
        mock_client_instance.download_as_text.return_value = json.dumps(mock_metadata)
        
        file_path = f"users/999/test_file.pdf"
        result = self.storage_service.download_file(file_path, self.test_user.id)
        
        self.assertFalse(result['success'])
        self.assertIn('Access denied', result['error'])
    
    @patch('services.gcp_storage_service.Client')
    def test_file_deletion(self, mock_client):
        """Test file deletion with cleanup"""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        # Mock metadata
        mock_metadata = {
            'user_id': self.test_user.id,
            'content_type': 'application/pdf'
        }
        mock_client_instance.download_as_text.return_value = json.dumps(mock_metadata)
        
        file_path = f"users/{self.test_user.id}/test_file.pdf"
        result = self.storage_service.delete_file(file_path, self.test_user.id)
        
        self.assertTrue(result['success'])
        
        # Verify deletion calls
        mock_client_instance.delete.assert_called()
    
    def test_signed_url_generation(self):
        """Test signed URL generation"""
        file_path = f"users/{self.test_user.id}/test_file.pdf"
        signed_url = self.storage_service.generate_signed_url(file_path, expires_in=3600)
        
        self.assertIsNotNone(signed_url)
        self.assertTrue(signed_url.startswith('/api/secure-download/'))
    
    def test_file_metadata_creation(self):
        """Test comprehensive file metadata creation"""
        metadata = self.storage_service._create_file_metadata(
            filename=self.test_filename,
            file_data=self.test_file_data,
            user_id=self.test_user.id,
            organization_id=None,
            file_category='invoice',
            file_path=f"users/{self.test_user.id}/test_file.pdf"
        )
        
        # Verify required fields
        self.assertEqual(metadata['filename'], self.test_filename)
        self.assertEqual(metadata['user_id'], self.test_user.id)
        self.assertEqual(metadata['category'], 'invoice')
        self.assertEqual(metadata['size'], len(self.test_file_data))
        self.assertIn('file_hash', metadata)
        self.assertIn('upload_timestamp', metadata)
        self.assertIn('compliance', metadata)
        self.assertIn('encryption', metadata)
    
    def test_file_validation(self):
        """Test file validation logic"""
        # Test valid file
        result = self.storage_service._validate_file(self.test_file_data, "document.pdf")
        self.assertTrue(result['valid'])
        
        # Test invalid file type
        result = self.storage_service._validate_file(self.test_file_data, "malicious.exe")
        self.assertFalse(result['valid'])
        
        # Test empty file
        result = self.storage_service._validate_file(b"", "empty.pdf")
        self.assertFalse(result['valid'])
    
    @patch('services.gcp_storage_service.Client')
    def test_bucket_policies_configuration(self, mock_client):
        """Test bucket policies configuration"""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        result = self.storage_service.configure_bucket_policies()
        
        self.assertTrue(result)
        mock_client_instance.upload_from_text.assert_called_once()
        
        # Verify policies content
        call_args = mock_client_instance.upload_from_text.call_args
        self.assertEqual(call_args[0][0], "bucket_policies.json")
        
        policies = json.loads(call_args[0][1])
        self.assertIn('retention_policy', policies)
        self.assertIn('lifecycle_rules', policies)
        self.assertIn('versioning', policies)
        self.assertIn('encryption', policies)
    
    def test_audit_logging(self):
        """Test audit trail logging"""
        # This would test the audit logging functionality
        # In a real implementation, you'd verify audit entries are created
        pass
    
    def test_compliance_features(self):
        """Test compliance and security features"""
        metadata = self.storage_service._create_file_metadata(
            filename=self.test_filename,
            file_data=self.test_file_data,
            user_id=self.test_user.id,
            organization_id=None,
            file_category='invoice',
            file_path=f"users/{self.test_user.id}/test_file.pdf"
        )
        
        # Verify compliance flags
        compliance = metadata['compliance']
        self.assertTrue(compliance['gdpr_compliant'])
        self.assertTrue(compliance['hipaa_compliant'])
        self.assertIn('retention_until', compliance)
        
        # Verify encryption
        encryption = metadata['encryption']
        self.assertTrue(encryption['encrypted_at_rest'])
        self.assertEqual(encryption['encryption_key'], 'replit-managed')
    
    def test_large_file_handling(self):
        """Test handling of large files with resumable uploads"""
        # This would test resumable upload functionality for large files
        # Implementation would depend on specific requirements
        pass

class TestStoragePerformance(unittest.TestCase):
    """Performance tests for storage operations"""
    
    def setUp(self):
        self.storage_service = GCPStorageService()
    
    @patch('services.gcp_storage_service.Client')
    def test_concurrent_uploads(self, mock_client):
        """Test concurrent upload handling"""
        # Test multiple simultaneous uploads
        # This would verify the system can handle concurrent operations
        pass
    
    @patch('services.gcp_storage_service.Client')
    def test_bulk_operations(self, mock_client):
        """Test bulk file operations"""
        # Test batch upload/download operations
        pass

class TestStorageSecurity(unittest.TestCase):
    """Security tests for storage implementation"""
    
    def setUp(self):
        self.storage_service = GCPStorageService()
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks"""
        malicious_filename = "../../../etc/passwd"
        safe_path = self.storage_service._generate_file_path(malicious_filename, 1)
        
        # Verify path doesn't contain traversal elements
        self.assertNotIn('..', safe_path)
        self.assertTrue(safe_path.startswith('users/1/'))
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        from werkzeug.utils import secure_filename
        
        dangerous_filename = "test<script>alert('xss')</script>.pdf"
        safe_filename = secure_filename(dangerous_filename)
        
        # Verify dangerous characters are removed
        self.assertNotIn('<', safe_filename)
        self.assertNotIn('>', safe_filename)
        self.assertNotIn('script', safe_filename)

if __name__ == '__main__':
    unittest.main()
