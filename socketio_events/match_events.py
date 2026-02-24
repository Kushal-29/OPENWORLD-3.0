"""
MATCH EVENTS - SIMPLIFIED & DIRECT
Works properly - no getting stuck
"""

from flask_socketio import emit, join_room
from flask_login import current_user
from flask import request
from models.models import db, User, MatchQueue, ActiveMatch
import logging
import time

logger = logging.getLogger(__name__)

# Simple tracking
online_users = {}  # {user_id: socket_id}
user_matches = {}  # {user_id: room_id}

def init_match_events(socketio):
    
    # ========== HELPERS ==========
    
    def get_other_user_id(room_id, current_user_id):
        """Get other user from room"""
        try:
            match = ActiveMatch.query.filter_by(room_id=room_id).first()
            if not match:
                return None
            return match.user2_id if match.user1_id == current_user_id else match.user1_id
        except:
            return None
    
    def is_match_active(room_id):
        """Check if match is active"""
        try:
            return ActiveMatch.query.filter_by(room_id=room_id, status='active').first() is not None
        except:
            return False
    
    def end_match(room_id):
        """End a match"""
        try:
            match = ActiveMatch.query.filter_by(room_id=room_id).first()
            if match:
                match.status = 'ended'
                match.ended_at = __import__('datetime').datetime.utcnow()
                
                # Clean up queue
                MatchQueue.query.filter(
                    MatchQueue.user_id.in_([match.user1_id, match.user2_id])
                ).delete()
                
                db.session.commit()
        except Exception as e:
            logger.error(f"Error ending match: {e}")
            db.session.rollback()
    
    # ========== CONNECT/DISCONNECT ==========
    
    @socketio.on("connect")
    def on_connect():
        if not current_user.is_authenticated:
            return False
        
        user_id = current_user.id
        online_users[user_id] = request.sid
        
        try:
            current_user.is_online = True
            current_user.socket_id = request.sid
            db.session.commit()
            logger.info(f"✅ Connected: {user_id}")
        except:
            db.session.rollback()
    
    @socketio.on("disconnect")
    def on_disconnect():
        if not current_user.is_authenticated:
            return
        
        user_id = current_user.id
        online_users.pop(user_id, None)
        
        # End any active match
        if user_id in user_matches:
            room_id = user_matches.pop(user_id)
            
            other_id = get_other_user_id(room_id, user_id)
            if other_id and other_id in online_users:
                socketio.emit("stranger_disconnected", 
                             {"message": "Stranger left"}, 
                             to=online_users[other_id])
                user_matches.pop(other_id, None)
            
            end_match(room_id)
        
        # Clean up queue
        try:
            MatchQueue.query.filter_by(user_id=user_id).delete()
            db.session.commit()
        except:
            db.session.rollback()
        
        # Update user
        try:
            current_user.is_online = False
            current_user.socket_id = None
            db.session.commit()
        except:
            db.session.rollback()
        
        logger.info(f"🔴 Disconnected: {user_id}")
    
    # ========== MATCHING LOGIC ==========
    
    @socketio.on("start_search")
    def start_search():
        """Main matching logic"""
        user_id = current_user.id
        logger.info(f"\n🔍 START_SEARCH: {user_id}\n")
        
        try:
            # Already in a match?
            if user_id in user_matches:
                logger.warning(f"  Already in match")
                emit("error", "Already in a match")
                return
            
            # Clean old queue entries
            try:
                MatchQueue.query.filter_by(user_id=user_id).delete()
                db.session.commit()
            except:
                db.session.rollback()
            
            # ===== STEP 1: Add self to queue =====
            logger.info(f"  Step 1: Adding to queue...")
            try:
                queue = MatchQueue(
                    user_id=user_id,
                    socket_id=request.sid,
                    status='waiting'
                )
                db.session.add(queue)
                db.session.commit()
                logger.info(f"  ✅ Added to queue")
            except Exception as e:
                logger.error(f"  ❌ Queue add failed: {e}")
                db.session.rollback()
                emit("error", "Failed to add to queue")
                return
            
            # Tell frontend we're searching
            emit("status", "🔍 Searching for a stranger...")
            
            # ===== STEP 2: Check for other waiting users =====
            logger.info(f"  Step 2: Looking for match...")
            try:
                # Get all waiting users except self
                waiting = MatchQueue.query.filter(
                    MatchQueue.user_id != user_id,
                    MatchQueue.status == 'waiting'
                ).all()
                
                logger.info(f"  Found {len(waiting)} waiting users")
                
                if not waiting:
                    logger.info(f"  No one waiting - user will wait")
                    return
                
                # Pick first one
                other_queue = waiting[0]
                other_user_id = other_queue.user_id
                other_socket = online_users.get(other_user_id)
                
                if not other_socket:
                    logger.warning(f"  Other user {other_user_id} not online, skipping")
                    MatchQueue.query.filter_by(user_id=other_user_id).delete()
                    db.session.commit()
                    return
                
            except Exception as e:
                logger.error(f"  ❌ Queue lookup failed: {e}")
                db.session.rollback()
                return
            
            # ===== STEP 3: Create match =====
            logger.info(f"  Step 3: Creating match {user_id} <-> {other_user_id}...")
            try:
                room_id = f"match_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}_{int(time.time() * 1000)}"
                
                # Update queue
                MatchQueue.query.filter_by(user_id=user_id).update({'status': 'matched'})
                MatchQueue.query.filter_by(user_id=other_user_id).update({'status': 'matched'})
                
                # Create active match
                match = ActiveMatch(
                    room_id=room_id,
                    user1_id=min(user_id, other_user_id),
                    user2_id=max(user_id, other_user_id),
                    status='active'
                )
                db.session.add(match)
                db.session.commit()
                
                logger.info(f"  ✅ Match created: {room_id}")
            except Exception as e:
                logger.error(f"  ❌ Match creation failed: {e}")
                db.session.rollback()
                emit("error", "Failed to create match")
                return
            
            # ===== STEP 4: Add to rooms and notify =====
            logger.info(f"  Step 4: Notifying users...")
            
            user_matches[user_id] = room_id
            user_matches[other_user_id] = room_id
            
            # Add to Socket.IO room
            join_room(room_id)
            socketio.server.enter_room(other_socket, room_id)
            
            # Get names
            other_user = User.query.get(other_user_id)
            other_name = other_user.full_name or other_user.username
            my_name = current_user.full_name or current_user.username
            
            # Send to initiator (self)
            emit("match_confirmed", {
                "room": room_id,
                "stranger_name": other_name,
                "stranger_id": other_user_id,
                "your_role": "initiator"
            })
            logger.info(f"  Sent match_confirmed to {user_id} (initiator)")
            
            # Send to receiver (other)
            socketio.emit("match_confirmed", {
                "room": room_id,
                "stranger_name": my_name,
                "stranger_id": user_id,
                "your_role": "receiver"
            }, to=other_socket)
            logger.info(f"  Sent match_confirmed to {other_user_id} (receiver)")
            
            logger.info(f"\n🎉 MATCH ACTIVE: {room_id}\n")
            
        except Exception as e:
            logger.error(f"\n❌ ERROR in start_search: {e}\n", exc_info=True)
            db.session.rollback()
            emit("error", f"Error: {str(e)}")
    
    # ========== SKIP ==========
    
    @socketio.on("skip_stranger")
    def skip_stranger():
        user_id = current_user.id
        logger.info(f"\n⏭️ SKIP: {user_id}\n")
        
        try:
            # End current match if any
            if user_id in user_matches:
                room_id = user_matches.pop(user_id)
                
                # Notify other
                other_id = get_other_user_id(room_id, user_id)
                if other_id and other_id in online_users:
                    socketio.emit("stranger_skipped",
                                 {"message": "Stranger skipped"},
                                 to=online_users[other_id])
                    user_matches.pop(other_id, None)
                
                end_match(room_id)
            
            # Restart search
            emit("status", "🔍 Searching for a stranger...")
            logger.info(f"  Auto-restarting search...")
            
            # Call start_search again to find another
            start_search()
            
        except Exception as e:
            logger.error(f"❌ Skip error: {e}")
            db.session.rollback()
    
    # ========== END CHAT ==========
    
    @socketio.on("end_chat")
    def end_chat():
        user_id = current_user.id
        logger.info(f"\n🛑 END: {user_id}\n")
        
        try:
            # End match
            if user_id in user_matches:
                room_id = user_matches.pop(user_id)
                
                # Notify other
                other_id = get_other_user_id(room_id, user_id)
                if other_id and other_id in online_users:
                    socketio.emit("stranger_disconnected",
                                 {"message": "Stranger ended chat"},
                                 to=online_users[other_id])
                    user_matches.pop(other_id, None)
                
                end_match(room_id)
            
            # Clear queue
            try:
                MatchQueue.query.filter_by(user_id=user_id).delete()
                db.session.commit()
            except:
                db.session.rollback()
            
            emit("status", '📱 Click "Start" to find a stranger')
            
        except Exception as e:
            logger.error(f"❌ End error: {e}")
            db.session.rollback()
    
    # ========== WEBRTC RELAY ==========
    
    @socketio.on("webrtc_offer")
    def on_offer(data):
        room = data.get("room")
        if is_match_active(room):
            logger.debug(f"📤 Relaying offer")
            emit("webrtc_offer", {"offer": data.get("offer")}, to=room, skip_sid=request.sid)
    
    @socketio.on("webrtc_answer")
    def on_answer(data):
        room = data.get("room")
        if is_match_active(room):
            logger.debug(f"📥 Relaying answer")
            emit("webrtc_answer", {"answer": data.get("answer")}, to=room, skip_sid=request.sid)
    
    @socketio.on("webrtc_ice_candidate")
    def on_ice(data):
        room = data.get("room")
        if is_match_active(room):
            logger.debug(f"🧊 Relaying ICE")
            emit("webrtc_ice_candidate", {"candidate": data.get("candidate")}, to=room, skip_sid=request.sid)
    
    # ========== FRIEND REQUEST ==========
    
    @socketio.on("send_friend_request_during_chat")
    def add_friend(data):
        user_id = current_user.id
        room = data.get("room")
        
        try:
            other_id = get_other_user_id(room, user_id)
            if not other_id:
                emit("error", "No match")
                return
            
            other = User.query.get(other_id)
            if not other:
                emit("error", "User not found")
                return
            
            # Add friend
            if not current_user.is_friend_with(other):
                current_user.add_friend(other)
                
                # Notify
                if other_id in online_users:
                    socketio.emit("friend_added_notification", {
                        "from_name": current_user.full_name or current_user.username
                    }, to=online_users[other_id])
            
            emit("status", f"✅ Added {other.full_name or other.username}!")
            logger.info(f"✅ Friends: {user_id} <-> {other_id}")
            
        except Exception as e:
            logger.error(f"Friend error: {e}")
            db.session.rollback()
            emit("error", str(e))