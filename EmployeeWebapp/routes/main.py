"""
Main routes — login / logout / dashboard.
"""

from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from auth import authenticate_ldap
from models import AuditLog, HardwareAsset, SoftwareAsset, User, db

main = Blueprint("main", __name__)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@main.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login via LDAP."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "warning")
            return render_template("login.html")

        ldap_info = authenticate_ldap(username, password)
        if ldap_info is None:
            flash("Invalid credentials. Please try again.", "danger")
            return render_template("login.html")

        # Create or update user record in the local database
        user = User.query.filter_by(username=ldap_info["username"]).first()
        if user is None:
            user = User(
                username=ldap_info["username"],
                display_name=ldap_info["display_name"],
                email=ldap_info["email"],
                role=ldap_info["role"],
            )
            db.session.add(user)
        else:
            user.display_name = ldap_info["display_name"]
            user.email = ldap_info["email"]
            user.role = ldap_info["role"]

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        if not user.is_active:
            flash("Your account has been deactivated. Contact an administrator.", "danger")
            return render_template("login.html")

        login_user(user)
        flash(f"Welcome back, {user.display_name or user.username}!", "success")

        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.dashboard"))

    return render_template("login.html")


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
@main.route("/logout")
@login_required
def logout():
    """Log the user out and redirect to the login page."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@main.route("/")
@main.route("/dashboard")
@login_required
def dashboard():
    """Render the main dashboard with summary statistics."""
    # Totals
    total_hardware = HardwareAsset.query.count()
    total_software = SoftwareAsset.query.count()
    deployed_hardware = HardwareAsset.query.filter_by(status="Deployed").count()
    active_software = SoftwareAsset.query.filter_by(status="Active").count()

    # Recent audit log entries
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    # Hardware grouped by status
    hardware_by_status = dict(
        db.session.query(HardwareAsset.status, func.count(HardwareAsset.id))
        .group_by(HardwareAsset.status)
        .all()
    )

    # Software grouped by status
    software_by_status = dict(
        db.session.query(SoftwareAsset.status, func.count(SoftwareAsset.id))
        .group_by(SoftwareAsset.status)
        .all()
    )

    return render_template(
        "dashboard.html",
        total_hardware=total_hardware,
        total_software=total_software,
        deployed_hardware=deployed_hardware,
        active_software=active_software,
        recent_logs=recent_logs,
        hardware_by_status=hardware_by_status,
        software_by_status=software_by_status,
    )
