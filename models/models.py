from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import pytz

db = SQLAlchemy()

# =========================
# FRIENDS ASSOCIATION
# =========================
friends_association = db.Table(
    'friends_association',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
)

# =========================
# BLOCKED USERS ASSOCIATION
# =========================
blocked_association = db.Table(
    'blocked_association',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('blocked_user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
)

# =========================
# USER MODEL
# =========================
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)

    # Profile Information
    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))  # male, female, other
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_pic = db.Column(db.String(200), default='default.png')
    
    # Interests (stored as comma-separated string)
    interests = db.Column(db.Text)  # "gaming,music,sports"
    
    # Reputation & Status
    reputation_score = db.Column(db.Float, default=5.0)  # 1.0-5.0
    
    # Online Status
    is_online = db.Column(db.Boolean, default=False)
    socket_id = db.Column(db.String(100))
    
    # Account Management
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    friends = db.relationship(
        'User',
        secondary=friends_association,
        primaryjoin=id == friends_association.c.user_id,
        secondaryjoin=id == friends_association.c.friend_id,
        lazy='dynamic'
    )

    blocked_users = db.relationship(
        'User',
        secondary=blocked_association,
        primaryjoin=id == blocked_association.c.user_id,
        secondaryjoin=id == blocked_association.c.blocked_user_id,
        lazy='dynamic'
    )

    sent_messages = db.relationship(
        'Message',
        foreign_keys='Message.sender_id',
        backref='sender',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    received_messages = db.relationship(
        'Message',
        foreign_keys='Message.receiver_id',
        backref='receiver',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    sent_requests = db.relationship(
        'FriendRequest',
        foreign_keys='FriendRequest.sender_id',
        backref='sender',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    received_requests = db.relationship(
        'FriendRequest',
        foreign_keys='FriendRequest.receiver_id',
        backref='receiver',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # ==================== METHODS ====================
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_friend_with(self, user):
        return self.friends.filter(
            friends_association.c.friend_id == user.id
        ).count() > 0

    def has_blocked(self, user):
        """Check if current user has blocked another user"""
        return self.blocked_users.filter(
            blocked_association.c.blocked_user_id == user.id
        ).count() > 0

    def block_user(self, user):
        """Block another user"""
        if not self.has_blocked(user):
            self.blocked_users.append(user)
            db.session.commit()

    def unblock_user(self, user):
        """Unblock a user"""
        if self.has_blocked(user):
            self.blocked_users.remove(user)
            db.session.commit()

    def add_friend(self, user):
        """Add another user as friend (bidirectional)"""
        if not self.is_friend_with(user):
            self.friends.append(user)
            user.friends.append(self)
            db.session.commit()

    def remove_friend(self, user):
        """Remove another user from friends"""
        if self.is_friend_with(user):
            self.friends.remove(user)
            user.friends.remove(self)
            db.session.commit()

    def get_interests_list(self):
        """Get interests as a list"""
        if not self.interests:
            return []
        return [i.strip() for i in self.interests.split(',')]

    def set_interests_list(self, interests_list):
        """Set interests from a list"""
        self.interests = ','.join(interests_list) if interests_list else None

    def last_seen_local(self, tz_name='Asia/Kolkata'):
        """Get last_seen time in specified timezone"""
        tz = pytz.timezone(tz_name)
        return self.last_seen.replace(tzinfo=pytz.utc).astimezone(tz)

    def __repr__(self):
        return f"<User {self.username}>"

# =========================
# MESSAGE MODEL
# =========================
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    text = db.Column(db.Text)
    image = db.Column(db.String(200))  # Filename for image
    document = db.Column(db.String(200))  # Filename for document
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Message {self.id}>"

# =========================
# FRIEND REQUEST MODEL
# =========================
class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FriendRequest {self.id}>"

# =========================
# MATCH QUEUE MODEL
# =========================
class MatchQueue(db.Model):
    __tablename__ = 'match_queue'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='queue_entries')
    
    status = db.Column(db.String(20), default='waiting')  # waiting, matched, cancelled
    
    # Preferences
    preferred_gender = db.Column(db.String(20), default='any')
    min_age = db.Column(db.Integer, default=13)
    max_age = db.Column(db.Integer, default=100)
    preferred_countries = db.Column(db.Text)  # JSON or comma-separated
    
    # Socket Info
    socket_id = db.Column(db.String(100))
    
    # Timeout
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    timeout_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))

    def __repr__(self):
        return f"<MatchQueue {self.user_id}>"

# =========================
# ACTIVE MATCH MODEL
# =========================
class ActiveMatch(db.Model):
    __tablename__ = 'active_matches'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(100), unique=True, nullable=False)
    
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    
    status = db.Column(db.String(20), default='active')  # active, ended
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

    def end_match(self):
        """End the match"""
        self.status = 'ended'
        self.ended_at = datetime.utcnow()
        db.session.commit()

    def duration_seconds(self):
        """Get match duration in seconds"""
        end = self.ended_at or datetime.utcnow()
        delta = end - self.started_at
        return int(delta.total_seconds())

    def __repr__(self):
        return f"<ActiveMatch {self.room_id}>"

# =========================
# MATCH HISTORY MODEL
# =========================
class MatchHistory(db.Model):
    __tablename__ = 'match_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    matched_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    user = db.relationship('User', foreign_keys=[user_id])
    matched_user = db.relationship('User', foreign_keys=[matched_user_id])
    
    room_id = db.Column(db.String(100))
    duration_seconds = db.Column(db.Integer, default=0)
    
    matched_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MatchHistory {self.user_id}-{self.matched_user_id}>"