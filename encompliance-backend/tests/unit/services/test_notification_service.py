"""
Notification Service Unit Tests
-------------------------------
Tests for notification service business logic
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.notification_service import NotificationService
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.schemas.notification import NotificationCreate


class TestNotificationService:
    """Test NotificationService methods"""
    
    @pytest.mark.asyncio
    @patch('app.services.notification_service.NotificationService._send_email_notification')
    @patch('app.services.notification_service.NotificationService._send_push_notification')
    async def test_create_notification_success(self, mock_push, mock_email, db: Session):
        """Test successful notification creation"""
        notification_data = NotificationCreate(
            title="Test Notification",
            message="Test message",
            type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL
        )
        
        notification = await NotificationService.create_notification(
            db, 
            notification_data, 
            user_id=1,
            send_email=False,
            send_push=False
        )
        
        assert notification.title == notification_data.title
        assert notification.message == notification_data.message
        assert notification.user_id == 1
    
    @pytest.mark.asyncio
    async def test_get_notifications_success(self, db: Session):
        """Test successful notifications retrieval"""
        # Create test notifications
        notif1 = Notification(
            title="Notification 1",
            message="Message 1",
            user_id=1,
            type=NotificationType.INFO
        )
        notif2 = Notification(
            title="Notification 2",
            message="Message 2",
            user_id=1,
            type=NotificationType.INFO
        )
        db.add(notif1)
        db.add(notif2)
        db.commit()
        
        result = await NotificationService.get_notifications(db, user_id=1)
        
        assert "notifications" in result
        assert "total" in result
        assert result["total"] >= 2
    
    @pytest.mark.asyncio
    async def test_get_notification_by_id_success(self, db: Session):
        """Test successful notification retrieval by ID"""
        notification = Notification(
            title="Test Notification",
            message="Test message",
            user_id=1,
            type=NotificationType.INFO
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        result = await NotificationService.get_notification(db, notification.id, user_id=1)
        
        assert result is not None
        assert result.id == notification.id
    
    @pytest.mark.asyncio
    async def test_mark_as_read_success(self, db: Session):
        """Test successful notification marking as read"""
        notification = Notification(
            title="Test Notification",
            message="Test message",
            user_id=1,
            type=NotificationType.INFO,
            is_read=False
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        result = await NotificationService.mark_as_read(db, notification.id, user_id=1)
        
        assert result is not None
        assert result.is_read == True
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read_success(self, db: Session):
        """Test marking all notifications as read"""
        notif1 = Notification(title="Note 1", message="Msg 1", user_id=1, type=NotificationType.INFO, is_read=False)
        notif2 = Notification(title="Note 2", message="Msg 2", user_id=1, type=NotificationType.INFO, is_read=False)
        db.add(notif1)
        db.add(notif2)
        db.commit()
        
        count = await NotificationService.mark_all_as_read(db, user_id=1)
        
        assert count >= 2
    
    @pytest.mark.asyncio
    async def test_get_unread_count_success(self, db: Session):
        """Test getting unread notification count"""
        notif1 = Notification(title="Note 1", message="Msg 1", user_id=1, type=NotificationType.INFO, is_read=False)
        notif2 = Notification(title="Note 2", message="Msg 2", user_id=1, type=NotificationType.INFO, is_read=True)
        db.add(notif1)
        db.add(notif2)
        db.commit()
        
        count = await NotificationService.get_unread_count(db, user_id=1)
        
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_delete_notification_success(self, db: Session):
        """Test successful notification deletion"""
        notification = Notification(
            title="To Delete",
            message="Content",
            user_id=1,
            type=NotificationType.INFO
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        result = await NotificationService.delete_notification(db, notification.id, user_id=1)
        
        assert result == True

