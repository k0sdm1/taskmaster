from functools import wraps
from flask import render_template
from flask_login import current_user

from models import User

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not User.query.get_or_404(current_user.get_id()).is_admin:
            return render_template("404.html"), 404
        return f(*args, **kwargs)
    return decorated_function
