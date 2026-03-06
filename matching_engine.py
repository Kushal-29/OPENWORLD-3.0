"""
MATCHING ENGINE - Simple, Direct, Working
"""

from models.models import db, ActiveMatch, MatchQueue
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StrangerMatcher:
    """Simple stranger matching"""
    
    @staticmethod
    def get_other_user_id(room_id, current_user_id):
        """Get the other user in a match"""
        try:
            match = ActiveMatch.query.filter_by(room_id=room_id).first()
            if not match:
                return None
            
            if match.user1_id == current_user_id:
                return match.user2_id
            else:
                return match.user1_id
        except Exception as e:
            logger.error(f"Error getting other user: {e}")
            return None
    
    @staticmethod
    def is_match_active(room_id):
        """Check if match is active"""
        try:
            match = ActiveMatch.query.filter_by(room_id=room_id, status='active').first()
            return match is not None
        except Exception as e:
            logger.error(f"Error checking match: {e}")
            return False
    
    @staticmethod
    def end_match(room_id):
        """End a match"""
        try:
            match = ActiveMatch.query.filter_by(room_id=room_id).first()
            if match:
                match.status = 'ended'
                match.ended_at = datetime.utcnow()
                
                # Remove both from queue
                MatchQueue.query.filter(
                    MatchQueue.user_id.in_([match.user1_id, match.user2_id])
                ).delete()
                
                db.session.commit()
                logger.info(f"✅ Match ended: {room_id}")
        except Exception as e:
            logger.error(f"Error ending match: {e}")
            db.session.rollback()