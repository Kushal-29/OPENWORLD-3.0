from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.models import db, User, FriendRequest

# =========================
# BLUEPRINT (MUST BE FIRST)
# =========================
friend_requests_bp = Blueprint(
    "friend_requests",
    __name__,
    url_prefix="/friend-requests"
)

# =========================
# FRIEND REQUESTS UI
# =========================
@friend_requests_bp.route("/ui")
@login_required
def requests_ui():
    try:
        requests = FriendRequest.query.filter_by(
            receiver_id=current_user.id,
            status="pending"
        ).all()

        return render_template(
            "friend_requests.html",
            requests=requests
        )
    except Exception as e:
        print(f"Requests UI error: {e}")
        return render_template("friend_requests.html", requests=[])

# =========================
# ACCEPT REQUEST
# =========================
@friend_requests_bp.route("/accept/<int:request_id>")
@login_required
def accept_request(request_id):
    try:
        fr = FriendRequest.query.get_or_404(request_id)

        if fr.receiver_id != current_user.id:
            flash("Unauthorized action", "error")
            return redirect(url_for("friend_requests.requests_ui"))

        sender = User.query.get(fr.sender_id)
        receiver = current_user

        if not sender:
            flash("User not found", "error")
            return redirect(url_for("friend_requests.requests_ui"))

        # Add friendship BOTH ways
        if sender not in receiver.friends:
            receiver.friends.append(sender)
            sender.friends.append(receiver)

        fr.status = "accepted"
        db.session.commit()

        flash(f"You are now friends with {sender.username}", "success")
        return redirect(url_for("chat.friends_list"))
    except Exception as e:
        print(f"Accept request error: {e}")
        db.session.rollback()
        flash("An error occurred while accepting the request", "error")
        return redirect(url_for("friend_requests.requests_ui"))

# =========================
# REJECT REQUEST
# =========================
@friend_requests_bp.route("/reject/<int:request_id>")
@login_required
def reject_request(request_id):
    try:
        fr = FriendRequest.query.get_or_404(request_id)

        if fr.receiver_id != current_user.id:
            flash("Unauthorized action", "error")
            return redirect(url_for("friend_requests.requests_ui"))

        fr.status = "rejected"
        db.session.commit()

        flash("Friend request rejected", "info")
        return redirect(url_for("friend_requests.requests_ui"))
    except Exception as e:
        print(f"Reject request error: {e}")
        db.session.rollback()
        flash("An error occurred while rejecting the request", "error")
        return redirect(url_for("friend_requests.requests_ui"))