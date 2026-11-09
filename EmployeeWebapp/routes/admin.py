"""
Admin routes — user management and role assignment.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

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
