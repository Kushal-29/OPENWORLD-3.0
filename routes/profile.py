from flask import Blueprint, render_template, redirect, request, flash, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.models import db, User
import os
from datetime import datetime
import pytz

profile_bp = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    """View user profile"""
    try:
        user = User.query.get_or_404(user_id)
        is_friend = current_user.is_friend_with(user) if user_id != current_user.id else False

        # Format last_seen in local timezone
        last_seen_local = user.last_seen_local()
        last_seen_formatted = last_seen_local.strftime("%B %d, %Y at %I:%M %p")

        return render_template(
            'profile.html',
            profile_user=user,
            is_friend=is_friend,
            last_seen=last_seen_formatted
        )
    except Exception as e:
        print(f"❌ View profile error: {e}")
        return redirect(url_for('profile.my_profile'))

@profile_bp.route('/profile')
@login_required
def my_profile():
    """View own profile"""
    try:
        return redirect(url_for('profile.view_profile', user_id=current_user.id))
    except Exception as e:
        print(f"❌ My profile error: {e}")
        return redirect(url_for('match.match_page'))

@profile_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit profile information"""
    
    try:
        if request.method == 'POST':
            # Update basic info
            current_user.full_name = request.form.get('full_name', '').strip()
            current_user.email = request.form.get('email', '').strip()
            
            # Update age (new field)
            age_str = request.form.get('age', '').strip()
            if age_str:
                try:
                    age = int(age_str)
                    if 13 <= age <= 120:
                        current_user.age = age
                    else:
                        flash('Age must be between 13 and 120', 'error')
                except ValueError:
                    flash('Age must be a number', 'error')
            else:
                current_user.age = None
            
            # Update gender (new field)
            current_user.gender = request.form.get('gender', '').strip() or None
            
            # Update location
            current_user.country = request.form.get('country', '').strip()
            current_user.city = request.form.get('city', '').strip()
            
            # Update bio
            current_user.bio = request.form.get('bio', '').strip()
            
            # Update interests (new field)
            interests_str = request.form.get('interests', '').strip()
            if interests_str:
                # Convert to comma-separated list
                interests_list = [i.strip() for i in interests_str.split(',')]
                current_user.set_interests_list(interests_list)
            else:
                current_user.interests = None
            
            # Handle profile picture upload
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    try:
                        # Create upload folder if it doesn't exist
                        os.makedirs('static/uploads/profiles', exist_ok=True)
                        
                        # Remove old profile pic if not default
                        if current_user.profile_pic != 'default.png':
                            old_pic_path = os.path.join('static/uploads/profiles', current_user.profile_pic)
                            if os.path.exists(old_pic_path):
                                os.remove(old_pic_path)
                        
                        # Save new profile pic
                        filename = secure_filename(f"{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}")
                        filepath = os.path.join('static/uploads/profiles', filename)
                        file.save(filepath)
                        current_user.profile_pic = filename
                        print(f"✅ Profile picture updated: {filename}")
                    except Exception as e:
                        print(f"❌ Profile pic upload error: {e}")
                        flash('Error uploading profile picture', 'error')
            
            db.session.commit()
            flash('✅ Profile updated successfully!', 'success')
            return redirect(url_for('profile.my_profile'))
        
        return render_template('edit_profile.html', user=current_user)
    except Exception as e:
        print(f"❌ Edit profile error: {e}")
        db.session.rollback()
        flash('An error occurred while editing your profile', 'error')
        return render_template('edit_profile.html', user=current_user)

@profile_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    try:
        return render_template('settings.html', user=current_user)
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return render_template('settings.html', user=current_user)