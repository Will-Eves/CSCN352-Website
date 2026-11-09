"""
Shared route decorators for role-based access control.
"""

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(*roles: str):
    """Decorator that restricts a view to users whose role is in *roles*.

    Usage::

        @role_required("admin")
        def admin_only_view(): ...

        @role_required("technician", "admin")
        def tech_or_admin_view(): ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                flash("You do not have permission to access this resource.", "danger")
                return redirect(url_for("main.dashboard"))
            return fn(*args, **kwargs)

        return wrapper

    return decorator
