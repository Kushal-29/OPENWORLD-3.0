from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from models.models import db, Message, User

def init_chat_events(socketio):

    @socketio.on('join_chat')
    def join_chat(data):
        try:
            room = data.get('room')
            if room:
                join_room(room)
                print(f"✅ User joined chat room: {room}")
        except Exception as e:
            print(f"❌ join_chat error: {e}")

    @socketio.on('send_message')
    def send_message(data):
        try:
            text = data.get('text', '').strip()
            receiver_id = data.get('receiver_id')
            room = data.get('room')
            image = data.get('image')
            document = data.get('document')

            # Must have receiver_id and room
            if not receiver_id or not room:
                emit('error', {'message': 'Invalid message data'})
                return

            # Must have at least text OR image OR document
            if not text and not image and not document:
                print("⚠️ Empty message (no text, image, or document)")
                return

            # Create message
            message = Message(
                sender_id=current_user.id,
                receiver_id=receiver_id,
                text=text if text else None,
                image=image if image else None,
                document=document if document else None,
                is_read=False
            )

            db.session.add(message)
            db.session.commit()

            # Get receiver info for notification
            receiver = User.query.get(receiver_id)

            # Emit to chat room (for people in chat window)
            emit('receive_message', {
                'id': message.id,
                'sender_id': current_user.id,
                'text': message.text,
                'image': message.image,
                'document': message.document,
                'timestamp': message.created_at.strftime('%H:%M'),
                'is_read': message.is_read
            }, room=room)

            # Emit notification popup to receiver (even if not in chat window)
            # Only if they're not in this chat room
            notification_data = {
                'sender_name': current_user.full_name or current_user.username,
                'sender_id': current_user.id,
                'message_text': (text or f"📎 Shared file")[:50],
                'sender_avatar': f"/static/uploads/profiles/{current_user.profile_pic}"
            }
            
            emit('message_notification', notification_data, to=f"user_{receiver_id}", skip_sid=True)

            # Update friends list for receiver
            emit('chat_list_update', {}, broadcast=True)

            print(f"✅ Message sent from {current_user.id} to {receiver_id}")

        except Exception as e:
            print(f"❌ send_message error: {e}")
            db.session.rollback()
            emit('error', {'message': 'Failed to send message'})

    @socketio.on('mark_as_read')
    def mark_as_read(data):
        """Mark messages as read"""
        try:
            message_id = data.get('message_id')
            if message_id:
                msg = Message.query.get(message_id)
                if msg and msg.receiver_id == current_user.id:
                    msg.is_read = True
                    db.session.commit()
                    
                    # Notify sender that message was read
                    emit('message_read', {
                        'message_id': message_id,
                        'sender_id': msg.sender_id
                    }, broadcast=True)
                    
                    print(f"✅ Message {message_id} marked as read")
        except Exception as e:
            print(f"❌ mark_as_read error: {e}")
            db.session.rollback()

    @socketio.on('leave_chat')
    def leave_chat(data):
        try:
            room = data.get('room')
            if room:
                leave_room(room)
                print(f"✅ User left chat room: {room}")
        except Exception as e:
            print(f"❌ leave_chat error: {e}")

    @socketio.on('user_connected')
    def user_connected():
        """Called when user connects - join their personal notification room"""
        try:
            if current_user.is_authenticated:
                join_room(f"user_{current_user.id}")
                print(f"✅ User {current_user.id} connected to notifications")
                emit('user_online', {
                    'user_id': current_user.id,
                    'username': current_user.username
                }, broadcast=True)
        except Exception as e:
            print(f"❌ user_connected error: {e}")