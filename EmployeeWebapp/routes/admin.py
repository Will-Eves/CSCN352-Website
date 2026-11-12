"""
Admin routes — user management and role assignment.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

from models import User, db, log_action
from routes.decorators import role_required

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@role_required("admin")
def admin_panel():
    """List all users with their roles."""
    users = User.query.order_by(User.username).all()
    return render_template("admin.html", users=users)


@admin_bp.route("/users/add", methods=["POST"])
@login_required
@role_required("admin")
def add_user():
    """Create a local webapp account."""
    username = request.form.get("username", "").strip()
    display_name = request.form.get("display_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")
    role = request.form.get("role", "viewer").strip()

    if not username or len(username) > 150:
        flash("Enter a username no longer than 150 characters.", "warning")
        return redirect(url_for("admin_bp.admin_panel"))

    existing_user = User.query.filter(
        db.func.lower(User.username) == username.lower()
    ).first()
    if existing_user is not None:
        flash(f"User '{existing_user.username}' is already registered.", "warning")
        return redirect(url_for("admin_bp.admin_panel"))

    if len(display_name) > 250 or len(email) > 250:
        flash("Name and email must be no longer than 250 characters.", "warning")
        return redirect(url_for("admin_bp.admin_panel"))
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "warning")
        return redirect(url_for("admin_bp.admin_panel"))
    if password != password_confirm:
        flash("Passwords do not match.", "warning")
        return redirect(url_for("admin_bp.admin_panel"))
    if role not in ("admin", "technician", "viewer"):
        flash("Select a valid role.", "warning")
        return redirect(url_for("admin_bp.admin_panel"))

    user = User(
        username=username,
        display_name=display_name or username,
        email=email or None,
        role=role,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    log_action(
        current_user.username,
        "CREATE",
        "user",
        user.id,
        {"username": username, "role": role, "account_type": "local"},
    )
    flash(f"User '{username}' has been added.", "success")
    return redirect(url_for("admin_bp.admin_panel"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@role_required("admin")
def update_user_role(user_id):
    """Update a user's role."""
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role", "").strip()

    if new_role not in ("admin", "technician", "viewer"):
        flash("Invalid role specified.", "warning")
        return redirect(url_for("admin_bp.admin_panel"))

    if user.id == current_user.id:
        flash("You cannot change your own role.", "warning")
        return redirect(url_for("admin_bp.admin_panel"))

    old_role = user.role
    user.role = new_role
    db.session.commit()

    log_action(
        current_user.username,
        "UPDATE",
        "user",
        user.id,
        {"field": "role", "old": old_role, "new": new_role},
    )
    flash(f"{user.display_name or user.username}'s role updated to {new_role}.", "success")
    return redirect(url_for("admin_bp.admin_panel"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_user_active(user_id):
    """Toggle a user's active status."""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin_bp.admin_panel"))

    user.is_active = not user.is_active
    db.session.commit()

    status_label = "activated" if user.is_active else "deactivated"
    log_action(
        current_user.username,
        "UPDATE",
        "user",
        user.id,
        {"field": "is_active", "new": user.is_active},
    )
    flash(f"{user.display_name or user.username} has been {status_label}.", "success")
    return redirect(url_for("admin_bp.admin_panel"))
