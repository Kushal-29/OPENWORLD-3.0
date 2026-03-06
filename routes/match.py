from flask import Blueprint, render_template
from flask_login import login_required

match_bp = Blueprint('match', __name__)

@match_bp.route('/match')
@login_required
def match_page():
    """Random video chat page"""
    return render_template('match.html')