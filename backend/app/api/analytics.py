# backend/app/api/analytics.py
"""
Analytics API endpoints for admin dashboard.
Time Complexity: O(n) where n is number of messages queried
Space Complexity: O(n) for result storage
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.database import db_service
from ..schemas.user import UserResponse
from .dependencies import get_current_active_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


async def get_admin_user(current_user: UserResponse = Depends(get_current_active_user)):
    """Verify user is admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/sentiment/overview")
async def get_sentiment_overview(
    days: int = Query(7, ge=1, le=90),
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    Get sentiment distribution over time.
    
    Business Value: Track team morale trends
    """
    db = db_service.get_admin_client()
    
    # Calculate date threshold
    date_threshold = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    # Get sentiment counts
    result = db.table('messages')\
        .select('sentiment, created_at')\
        .gte('created_at', date_threshold)\
        .not_.is_('sentiment', 'null')\
        .execute()
    
    if not result.data:
        return {
            "total_messages": 0,
            "sentiment_distribution": {},
            "daily_trends": []
        }
    
    # Count sentiments
    sentiment_counts = {}
    for msg in result.data:
        sentiment = msg['sentiment']
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    # Calculate daily trends
    daily_data = {}
    for msg in result.data:
        date = msg['created_at'][:10]  # Get YYYY-MM-DD
        if date not in daily_data:
            daily_data[date] = {"positive": 0, "negative": 0, "neutral": 0}
        daily_data[date][msg['sentiment']] += 1
    
    daily_trends = [
        {"date": date, **counts}
        for date, counts in sorted(daily_data.items())
    ]
    
    return {
        "total_messages": len(result.data),
        "sentiment_distribution": sentiment_counts,
        "daily_trends": daily_trends,
        "period_days": days
    }


@router.get("/sentiment/negative-alerts")
async def get_negative_alerts(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    Get recent negative messages for admin intervention.
    
    Business Value: Early conflict detection
    """
    db = db_service.get_admin_client()
    
    result = db.table('messages')\
        .select('*, users!messages_sender_id_fkey(username), chat_rooms(name)')\
        .eq('sentiment', 'negative')\
        .order('created_at', desc=True)\
        .limit(limit)\
        .execute()
    
    alerts = []
    for msg in result.data:
        alerts.append({
            "message_id": msg['id'],
            "content": msg['content'],
            "sender": msg['users']['username'],
            "chat_room": msg['chat_rooms']['name'] if msg['chat_rooms']['name'] else 'Direct Message',
            "timestamp": msg['created_at']
        })
    
    return {"negative_messages": alerts}


@router.get("/sentiment/by-user")
async def get_sentiment_by_user(
    days: int = Query(7, ge=1, le=90),
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    Get sentiment breakdown by user.
    
    Business Value: Identify team members who may need support
    """
    db = db_service.get_admin_client()
    
    date_threshold = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    result = db.table('messages')\
        .select('sender_id, sentiment, users!messages_sender_id_fkey(username)')\
        .gte('created_at', date_threshold)\
        .not_.is_('sentiment', 'null')\
        .execute()
    
    user_sentiments = {}
    for msg in result.data:
        user_id = msg['sender_id']
        if user_id not in user_sentiments:
            user_sentiments[user_id] = {
                "username": msg['users']['username'],
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "total": 0
            }
        user_sentiments[user_id][msg['sentiment']] += 1
        user_sentiments[user_id]['total'] += 1
    
    # Calculate sentiment percentages
    user_stats = []
    for user_id, data in user_sentiments.items():
        total = data['total']
        user_stats.append({
            "user_id": user_id,
            "username": data['username'],
            "positive_count": data['positive'],
            "negative_count": data['negative'],
            "neutral_count": data['neutral'],
            "total_messages": total,
            "positive_percent": round((data['positive'] / total) * 100, 1),
            "negative_percent": round((data['negative'] / total) * 100, 1),
            "sentiment_score": round(((data['positive'] - data['negative']) / total) * 100, 1)
        })
    
    # Sort by sentiment score (most negative first)
    user_stats.sort(key=lambda x: x['sentiment_score'])
    
    return {"user_sentiments": user_stats}


@router.get("/stats/overall")
async def get_overall_stats(
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    Get overall chat statistics.
    
    Business Value: Platform health metrics
    """
    db = db_service.get_admin_client()
    
    # Total users
    users = db.table('users').select('id', count='exact').execute()
    
    # Total messages
    messages = db.table('messages').select('id', count='exact').execute()
    
    # Total chat rooms
    rooms = db.table('chat_rooms').select('id', count='exact').execute()
    
    # Messages today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    messages_today = db.table('messages')\
        .select('id', count='exact')\
        .gte('created_at', today)\
        .execute()
    
    return {
        "total_users": users.count,
        "total_messages": messages.count,
        "total_chat_rooms": rooms.count,
        "messages_today": messages_today.count
    }