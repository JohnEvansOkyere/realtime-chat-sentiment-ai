# backend/app/api/analytics.py
"""
Analytics API endpoints for admin dashboard.
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
    """Get sentiment distribution over time."""
    db = db_service.get_admin_client()
    
    try:
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
    
    except Exception as e:
        print(f"ERROR in get_sentiment_overview: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sentiment/negative-alerts")
async def get_negative_alerts(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_admin_user)
):
    """Get recent negative messages."""
    db = db_service.get_admin_client()
    
    try:
        result = db.table('messages')\
            .select('id, content, sender_id, chat_room_id, created_at')\
            .eq('sentiment', 'negative')\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        alerts = []
        for msg in result.data:
            # Get sender username
            sender = db.table('users')\
                .select('username')\
                .eq('id', msg['sender_id'])\
                .single()\
                .execute()
            
            # Get chat room name
            room = db.table('chat_rooms')\
                .select('name')\
                .eq('id', msg['chat_room_id'])\
                .single()\
                .execute()
            
            alerts.append({
                "message_id": msg['id'],
                "content": msg['content'],
                "sender": sender.data['username'] if sender.data else 'Unknown',
                "chat_room": room.data['name'] if room.data and room.data['name'] else 'Direct Message',
                "timestamp": msg['created_at']
            })
        
        return {"negative_messages": alerts}
    
    except Exception as e:
        print(f"ERROR in get_negative_alerts: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# backend/app/api/analytics.py
# Update get_sentiment_by_user function:

@router.get("/sentiment/by-user")
async def get_sentiment_by_user(
    days: int = Query(7, ge=1, le=90),
    current_user: UserResponse = Depends(get_admin_user)
):
    """Get sentiment breakdown by user."""
    db = db_service.get_admin_client()
    
    try:
        date_threshold = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        result = db.table('messages')\
            .select('sender_id, sentiment')\
            .gte('created_at', date_threshold)\
            .not_.is_('sentiment', 'null')\
            .execute()
        
        # Valid sentiments only
        valid_sentiments = {'positive', 'negative', 'neutral'}
        
        user_sentiments = {}
        for msg in result.data:
            sentiment = msg['sentiment']
            
            # Skip invalid sentiments
            if sentiment not in valid_sentiments:
                continue
            
            user_id = msg['sender_id']
            if user_id not in user_sentiments:
                user_sentiments[user_id] = {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "total": 0
                }
            user_sentiments[user_id][sentiment] += 1
            user_sentiments[user_id]['total'] += 1
        
        # Calculate sentiment percentages and get usernames
        user_stats = []
        for user_id, data in user_sentiments.items():
            # Get username
            user = db.table('users')\
                .select('username')\
                .eq('id', user_id)\
                .single()\
                .execute()
            
            username = user.data['username'] if user.data else 'Unknown'
            
            total = data['total']
            if total == 0:
                continue
                
            user_stats.append({
                "user_id": user_id,
                "username": username,
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
    
    except Exception as e:
        print(f"ERROR in get_sentiment_by_user: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sentiment/overview")
async def get_sentiment_overview(
    days: int = Query(7, ge=1, le=90),
    current_user: UserResponse = Depends(get_admin_user)
):
    """Get sentiment distribution over time."""
    db = db_service.get_admin_client()
    
    try:
        # Calculate date threshold
        date_threshold = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Valid sentiments only
        valid_sentiments = {'positive', 'negative', 'neutral'}
        
        # Get sentiment counts
        result = db.table('messages')\
            .select('sentiment, created_at')\
            .gte('created_at', date_threshold)\
            .not_.is_('sentiment', 'null')\
            .execute()
        
        # Filter valid sentiments
        messages = [msg for msg in result.data if msg['sentiment'] in valid_sentiments]
        
        if not messages:
            return {
                "total_messages": 0,
                "sentiment_distribution": {},
                "daily_trends": []
            }
        
        # Count sentiments
        sentiment_counts = {}
        for msg in messages:
            sentiment = msg['sentiment']
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Calculate daily trends
        daily_data = {}
        for msg in messages:
            date = msg['created_at'][:10]  # Get YYYY-MM-DD
            if date not in daily_data:
                daily_data[date] = {"positive": 0, "negative": 0, "neutral": 0}
            daily_data[date][msg['sentiment']] += 1
        
        daily_trends = [
            {"date": date, **counts}
            for date, counts in sorted(daily_data.items())
        ]
        
        return {
            "total_messages": len(messages),
            "sentiment_distribution": sentiment_counts,
            "daily_trends": daily_trends,
            "period_days": days
        }
    
    except Exception as e:
        print(f"ERROR in get_sentiment_overview: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/stats/overall")
async def get_overall_stats(
    current_user: UserResponse = Depends(get_admin_user)
):
    """Get overall chat statistics."""
    db = db_service.get_admin_client()
    
    try:
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
            "total_users": users.count or 0,
            "total_messages": messages.count or 0,
            "total_chat_rooms": rooms.count or 0,
            "messages_today": messages_today.count or 0
        }
    
    except Exception as e:
        print(f"ERROR in get_overall_stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )