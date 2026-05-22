from functools import wraps

from flask import redirect, request, session, url_for

from app.models import User, db


def ensure_default_admin(username="admin", password="admin123"):
    user = User.query.filter_by(username=username).first()
    if user:
        return user
    user = User(username=username, role="admin", display_name="系统管理员")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped
