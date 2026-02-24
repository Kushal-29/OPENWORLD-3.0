from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_, desc
from models.models import db, User, Message

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat/<int:user_id>')
@login_required
def chat_window(user_id):
    try:
        friend = User.query.get_or_404(user_id)

        if not current_user.is_friend_with(friend):
            return redirect(url_for('chat.friends_list'))

        messages = Message.query.filter(
            or_(
                (Message.sender_id == current_user.id) & (Message.receiver_id == user_id),
                (Message.sender_id == user_id) & (Message.receiver_id == current_user.id)
            )
        ).order_by(Message.created_at).all()

        # Mark all messages as read when user views chat
        for msg in messages:
            if msg.receiver_id == current_user.id and not msg.is_read:
                msg.is_read = True
        
        db.session.commit()

        return render_template(
            'chat.html',
            friend=friend,
            messages=messages,
            user=current_user
        )
    except Exception as e:
        print(f"Chat window error: {e}")
        return redirect(url_for('chat.friends_list'))

@chat_bp.route('/friends')
@login_required
def friends_list():
    try:
        friends = current_user.friends.all()

        conversations = []
        for friend in friends:
            last_msg = Message.query.filter(
                or_(
                    (Message.sender_id == current_user.id) & (Message.receiver_id == friend.id),
                    (Message.sender_id == friend.id) & (Message.receiver_id == current_user.id)
                )
            ).order_by(desc(Message.created_at)).first()

            # Only count UNREAD messages (is_read == False)
            unread_count = Message.query.filter(
                Message.sender_id == friend.id,
                Message.receiver_id == current_user.id,
                Message.is_read == False  # Only unread messages
            ).count()

            conversations.append({
                "friend": friend,
                "last_msg": last_msg,
                "unread": unread_count  # Will be 0 if all read
            })

        return render_template(
            'friends.html',
            conversations=conversations,
            user=current_user
        )
    except Exception as e:
        print(f"Friends list error: {e}")
        return render_template('friends.html', conversations=[], user=current_user)