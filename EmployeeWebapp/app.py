"""
Rage N Raze — Employee IT Asset Management Webapp
Application factory and entry point.
"""

import os

from flask import Flask
from sqlalchemy import inspect, text

from auth import init_login_manager
from config import Config
from models import Category, db


def create_app() -> Flask:
    """Application factory: configure, initialise extensions, register
    blueprints, seed default data, and return the Flask app."""

    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure the instance folder exists (for SQLite database)
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance")
    os.makedirs(instance_path, exist_ok=True)

    # ── Extensions ──────────────────────────────────────────────────────
    db.init_app(app)
    init_login_manager(app)

    # ── Blueprints ──────────────────────────────────────────────────────
    from routes.admin import admin_bp
    from routes.assets import assets
    from routes.categories import categories
    from routes.main import main

    app.register_blueprint(main)
    app.register_blueprint(assets)
    app.register_blueprint(categories)
    app.register_blueprint(admin_bp)

    # ── Database & Seed Data ────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        user_columns = {
            column["name"] for column in inspect(db.engine).get_columns("users")
        }
        if "password_hash" not in user_columns:
            db.session.execute(
                text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
            )
            db.session.commit()
        _seed_default_categories()

    # ── Template Context Processor ──────────────────────────────────────
    @app.context_processor
    def inject_role_helpers():
        """Make role-checking helpers available in every template."""
        from flask_login import current_user as _cu

        def is_admin():
            return _cu.is_authenticated and _cu.role == "admin"

        def is_technician():
            return _cu.is_authenticated and _cu.role == "technician"

        def is_viewer():
            return _cu.is_authenticated and _cu.role == "viewer"

        def can_edit():
            return _cu.is_authenticated and _cu.role in ("admin", "technician")

        def can_delete():
            return _cu.is_authenticated and _cu.role == "admin"

        return {
            "is_admin": is_admin,
            "is_technician": is_technician,
            "is_viewer": is_viewer,
            "can_edit": can_edit,
            "can_delete": can_delete,
        }

    return app


# ── Seed helpers ────────────────────────────────────────────────────────

def _seed_default_categories():
    """Populate the categories table with defaults when the DB is empty."""
    if Category.query.first() is not None:
        return  # Already seeded

    hardware_categories = [
        "Desktop",
        "Laptop",
        "Monitor",
        "Printer",
        "Networking",
        "Server",
        "Peripheral",
        "Mobile Device",
    ]
    software_categories = [
        "Operating System",
        "Productivity",
        "Security",
        "Development",
        "Communication",
        "Database",
        "Utilities",
    ]

    for name in hardware_categories:
        db.session.add(Category(name=name, asset_type="hardware"))
    for name in software_categories:
        db.session.add(Category(name=name, asset_type="software"))

    db.session.commit()


# ── WSGI Application Instance ───────────────────────────────────────────
# Expose module-level 'app' for WSGI servers (IIS HttpPlatformHandler, Waitress, WFastCGI)
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
