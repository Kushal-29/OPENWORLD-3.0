from flask_socketio import emit, join_room
from flask_login import current_user
from models.models import db, User, FriendRequest

def init_friend_events(socketio):
    """Friend request and friend management events"""
    
    @socketio.on('send_friend_request')
    def send_friend_request(data):
        """Send friend request from video match"""
        try:
            receiver_id = data.get('receiver_id')
            room = data.get('room')
            
            if not receiver_id:
                emit('error', 'Invalid request')
                return
            
            receiver = User.query.get(receiver_id)
            if not receiver:
                emit('error', 'User not found')
                return
            
            # Check if already friends
            if current_user.is_friend_with(receiver):
                emit('error', 'Already friends')
                return
            
            # Check if request already exists
            existing_request = FriendRequest.query.filter(
                (FriendRequest.sender_id == current_user.id) & 
                (FriendRequest.receiver_id == receiver_id) &
                (FriendRequest.status == 'pending')
            ).first()
            
            if existing_request:
                emit('error', 'Friend request already sent')
                return
            
            # Create friend request
            friend_req = FriendRequest(
                sender_id=current_user.id,
                receiver_id=receiver_id
            )
            
            db.session.add(friend_req)
            db.session.commit()
            
            # Notify sender
            emit('friend_request_sent', {
                'message': f'Friend request sent to {receiver.username}',
                'receiver_id': receiver_id
            }, room=room)
            
            # Notify receiver (they'll get it when they come online)
            emit('friend_request_received', {
                'sender_id': current_user.id,
                'sender_name': current_user.username,
                'sender_pic': current_user.profile_pic
            }, room=f'user_{receiver_id}')
            
            print(f"✅ Friend request sent: {current_user.id} -> {receiver_id}")
        
        except Exception as e:
            print(f"❌ send_friend_request error: {e}")
            emit('error', f'Failed to send request: {str(e)}')
    
    @socketio.on('add_friend_direct')
    def add_friend_direct(data):
        """Both users agree to add each other as friends (from chat/profile)"""
        try:
            friend_id = data.get('friend_id')
            room = data.get('room')
            
            friend = User.query.get(friend_id)
            if not friend:
                emit('error', 'User not found')
                return
            
            # Use the add_friend method from User model
            current_user.add_friend(friend)
            
            # Notify both users
            emit('friend_added_success', {
                'message': f'You are now friends with {friend.username}!',
                'friend': {
                    'id': friend.id,
                    'username': friend.username,
                    'profile_pic': friend.profile_pic
                }
            }, room=room)
            
            print(f"✅ Friends added: {current_user.id} <-> {friend_id}")
        
        except Exception as e:
            print(f"❌ add_friend_direct error: {e}")
            emit('error', f'Failed to add friend: {str(e)}')
    
    @socketio.on('accept_friend_request')
    def accept_friend_request(data):
        """Accept incoming friend request"""
        try:
            sender_id = data.get('sender_id')
            
            friend = User.query.get(sender_id)
            if not friend:
                emit('error', 'User not found')
                return
            
            # Update friend request status
            friend_req = FriendRequest.query.filter(
                (FriendRequest.sender_id == sender_id) &
                (FriendRequest.receiver_id == current_user.id) &
                (FriendRequest.status == 'pending')
            ).first()
            
            if not friend_req:
                emit('error', 'Friend request not found')
                return
            
            friend_req.status = 'accepted'
            
            # Use the add_friend method from User model
            current_user.add_friend(friend)
            
            # Notify sender
            emit('friend_request_accepted', {
                'message': f'{current_user.username} accepted your friend request!',
                'friend': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'profile_pic': current_user.profile_pic
                }
            }, room=f'user_{sender_id}')
            
            # Notify receiver
            emit('friend_added_success', {
                'message': f'You are now friends with {friend.username}!'
            })
            
            print(f"✅ Friend request accepted: {current_user.id} accepted {sender_id}")
        
        except Exception as e:
            print(f"❌ accept_friend_request error: {e}")
            emit('error', f'Failed to accept request: {str(e)}')
    
    @socketio.on('reject_friend_request')
    def reject_friend_request(data):
        """Reject incoming friend request"""
        try:
            sender_id = data.get('sender_id')
            
            friend_req = FriendRequest.query.filter(
                (FriendRequest.sender_id == sender_id) &
                (FriendRequest.receiver_id == current_user.id) &
                (FriendRequest.status == 'pending')
            ).first()
            
            if not friend_req:
                emit('error', 'Friend request not found')
                return
            
            friend_req.status = 'rejected'
            db.session.commit()
            
            emit('friend_request_rejected', {
                'message': f'{current_user.username} rejected your friend request'
            }, room=f'user_{sender_id}')
            
            print(f"✅ Friend request rejected: {current_user.id} rejected {sender_id}")
        
        except Exception as e:
            print(f"❌ reject_friend_request error: {e}")
            emit('error', f'Failed to reject request: {str(e)}')
    
    @socketio.on('block_user')
    def block_user(data):
        """Block another user"""
        try:
            user_id = data.get('user_id')
            
            user = User.query.get(user_id)
            if not user:
                emit('error', 'User not found')
                return
            
            current_user.block_user(user)
            emit('user_blocked', {'user_id': user_id})
            
            print(f"✅ User blocked: {current_user.id} blocked {user_id}")
        
        except Exception as e:
            print(f"❌ block_user error: {e}")
            emit('error', f'Failed to block user: {str(e)}')
    
    @socketio.on('unblock_user')
    def unblock_user(data):
        """Unblock a user"""
        try:
            user_id = data.get('user_id')
            
            user = User.query.get(user_id)
            if not user:
                emit('error', 'User not found')
                return
            
            current_user.unblock_user(user)
            emit('user_unblocked', {'user_id': user_id})
            
            print(f"✅ User unblocked: {current_user.id} unblocked {user_id}")
        
        except Exception as e:
            print(f"❌ unblock_user error: {e}")
            emit('error', f'Failed to unblock user: {str(e)}')