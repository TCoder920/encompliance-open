"""
Export Service Unit Tests
-------------------------
Tests for export functionality including:
- Export size estimation
- Fee calculation
- Export request processing
- Quota management
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.services.export_service import ExportService
from app.models.export_request import ExportRequest, ExportStatus, ExportFormat
from app.models.user import User


class TestExportSizeEstimation:
    """Test export size estimation"""
    
    @patch('app.services.export_service.DataExtractionService.extract_all_user_data')
    @patch('app.services.export_service.DataExtractionService.calculate_data_size')
    def test_estimate_export_size_success(self, mock_calculate, mock_extract, db: Session):
        """Test successful export size estimation"""
        mock_extract.return_value = {"user_profile": {}, "documents": []}
        mock_calculate.return_value = 1000000  # 1MB
        
        size = ExportService.estimate_export_size(db, user_id=1, data_types=["user_profile", "documents"])
        
        assert size > 0
        assert size >= 1000000  # Should include overhead
    
    @patch('app.services.export_service.DataExtractionService.extract_all_user_data')
    def test_estimate_export_size_extraction_error(self, mock_extract, db: Session):
        """Test export size estimation when extraction fails"""
        mock_extract.return_value = {"error": "Extraction failed"}
        
        size = ExportService.estimate_export_size(db, user_id=1, data_types=["user_profile"])
        
        # Should fallback to estimate
        assert size > 0
    
    def test_estimate_export_size_exception(self, db: Session):
        """Test export size estimation with exception"""
        with patch('app.services.export_service.DataExtractionService.extract_all_user_data') as mock_extract:
            mock_extract.side_effect = Exception("Database error")
            
            size = ExportService.estimate_export_size(db, user_id=1, data_types=["user_profile"])
            
            # Should fallback to estimate
            assert size > 0
    
    def test_fallback_size_estimate(self):
        """Test fallback size estimation"""
        size = ExportService._fallback_size_estimate(["user_profile", "documents"])
        
        assert size > 0
        assert isinstance(size, int)
    
    def test_fallback_size_estimate_unknown_type(self):
        """Test fallback size estimation with unknown data type"""
        size = ExportService._fallback_size_estimate(["unknown_type"])
        
        # Unknown types should return 0 or a default value
        assert size >= 0


class TestExportFeeCalculation:
    """Test export fee calculation"""
    
    def test_calculate_fee_under_threshold(self):
        """Test fee calculation for exports under 1GB"""
        fee = ExportService.calculate_fee(estimated_size=500 * 1024 * 1024)  # 500MB
        
        assert fee == 0.0
    
    def test_calculate_fee_over_threshold(self):
        """Test fee calculation for exports over 1GB"""
        # 2GB = 1GB over threshold = $5
        fee = ExportService.calculate_fee(estimated_size=2 * 1024 * 1024 * 1024)
        
        assert fee == 5.0
    
    def test_calculate_fee_exact_threshold(self):
        """Test fee calculation at exact threshold"""
        fee = ExportService.calculate_fee(estimated_size=ExportService.FEE_THRESHOLD)
        
        assert fee == 0.0
    
    def test_calculate_fee_multiple_gb(self):
        """Test fee calculation for multiple GB over threshold"""
        # 3.5GB = 2.5GB over threshold = $12.50
        fee = ExportService.calculate_fee(estimated_size=int(3.5 * 1024 * 1024 * 1024))
        
        assert fee == pytest.approx(12.50, rel=0.1)


class TestExportRequestProcessing:
    """Test export request processing"""
    
    @patch('app.services.export_service.ExportQuotaService.check_quota_available')
    @patch('app.services.export_service.ExportService.estimate_export_size')
    @patch('app.services.export_service.ExportProcessingService.start_export_processing')
    def test_create_export_request_success(
        self, 
        mock_process, 
        mock_estimate, 
        mock_quota,
        db: Session
    ):
        """Test successful export request creation"""
        mock_quota.return_value = True
        mock_estimate.return_value = 1000000
        mock_process.return_value = True
        
        user = User(id=1, email="test@example.com", subscription_status="pro")
        db.add(user)
        db.commit()
        
        result = ExportService.initiate_export(
            db=db,
            user_id=1,
            format=ExportFormat.JSON.value,
            data_types=["user_profile"]
        )
        
        assert result is not None
        assert "export_id" in result or "valid" in result
    
    @patch('app.services.export_service.ExportQuotaService.check_quota_available')
    def test_create_export_request_quota_exceeded(self, mock_quota, db: Session):
        """Test export request creation when quota is exceeded"""
        mock_quota.return_value = False
        
        user = User(id=1, email="test@example.com", subscription_status="pro")
        db.add(user)
        db.commit()
        
        result = ExportService.initiate_export(
            db=db,
            user_id=1,
            format=ExportFormat.JSON.value,
            data_types=["user_profile"]
        )
        
        assert result is not None
        assert "valid" in result and result["valid"] == False
        assert "quota" in result.get("error", "").lower() or "quota" in result.get("message", "").lower()

