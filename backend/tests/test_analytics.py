# backend/tests/test_analytics.py
"""
Unit tests for analytics endpoints.
Coverage: Overall Stats, Sentiment Overview, Negative Alerts, User Sentiment
"""
import pytest
from unittest.mock import patch
from fastapi import status


class TestOverallStats:
    """Tests for overall statistics endpoint."""
    
    def test_get_overall_stats_success(self, client, override_get_admin_user, mock_db):
        """Test getting overall stats as admin."""
        with patch('app.models.database.db_service.get_admin_client', return_value=mock_db):
            # Mock counts
            mock_db.table.return_value.select.return_value.execute.return_value.count = 10
            
            response = client.get("/api/v1/analytics/stats/overall")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "total_users" in data
            assert "total_messages" in data
    
    def test_get_overall_stats_not_admin(self, client, override_get_current_user):
        """Test getting stats as non-admin user."""
        response = client.get("/api/v1/analytics/stats/overall")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_overall_stats_no_auth(self, client):
        """Test getting stats without authentication."""
        response = client.get("/api/v1/analytics/stats/overall")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSentimentOverview:
    """Tests for sentiment overview endpoint."""
    
    def test_get_sentiment_overview_success(self, client, admin_auth_headers, mock_db):
        """Test getting sentiment overview."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock messages with sentiment
            mock_db.table.return_value.select.return_value.gte.return_value.not_.return_value.execute.return_value.data = [
                {"sentiment": "positive", "created_at": "2024-01-01T00:00:00"},
                {"sentiment": "positive", "created_at": "2024-01-01T00:00:00"},
                {"sentiment": "negative", "created_at": "2024-01-01T00:00:00"},
                {"sentiment": "neutral", "created_at": "2024-01-02T00:00:00"},
            ]
            
            response = client.get(
                "/api/v1/analytics/sentiment/overview?days=7",
                headers=admin_auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "sentiment_distribution" in data
            assert "daily_trends" in data
            assert data["total_messages"] > 0
    
    def test_get_sentiment_overview_custom_days(self, client, admin_auth_headers, mock_db):
        """Test sentiment overview with custom day range."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.gte.return_value.not_.return_value.execute.return_value.data = []
            
            response = client.get(
                "/api/v1/analytics/sentiment/overview?days=30",
                headers=admin_auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["period_days"] == 30
    
    def test_get_sentiment_overview_invalid_days(self, client, admin_auth_headers):
        """Test sentiment overview with invalid day range."""
        response = client.get(
            "/api/v1/analytics/sentiment/overview?days=999",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestNegativeAlerts:
    """Tests for negative message alerts."""
    
    def test_get_negative_alerts_success(self, client, admin_auth_headers, mock_db):
        """Test getting negative message alerts."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock negative messages
            mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
                {
                    "id": "msg1",
                    "content": "This is terrible",
                    "sender_id": "user1",
                    "chat_room_id": "room1",
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
            
            # Mock user and room data
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                "username": "testuser"
            }
            
            response = client.get(
                "/api/v1/analytics/sentiment/negative-alerts?limit=10",
                headers=admin_auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "negative_messages" in data
    
    def test_get_negative_alerts_empty(self, client, admin_auth_headers, mock_db):
        """Test negative alerts when no negative messages."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
            
            response = client.get(
                "/api/v1/analytics/sentiment/negative-alerts",
                headers=admin_auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["negative_messages"] == []


class TestUserSentiment:
    """Tests for user sentiment analysis."""
    
    def test_get_user_sentiment_success(self, client, admin_auth_headers, mock_db):
        """Test getting sentiment breakdown by user."""
        with patch('app.services.chat_service.db_service.get_admin_client', return_value=mock_db):
            # Mock messages
            mock_db.table.return_value.select.return_value.gte.return_value.not_.return_value.execute.return_value.data = [
                {"sender_id": "user1", "sentiment": "positive"},
                {"sender_id": "user1", "sentiment": "positive"},
                {"sender_id": "user1", "sentiment": "negative"},
                {"sender_id": "user2", "sentiment": "neutral"},
            ]
            
            # Mock user data
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                "username": "testuser"
            }
            
            response = client.get(
                "/api/v1/analytics/sentiment/by-user?days=7",
                headers=admin_auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "user_sentiments" in data