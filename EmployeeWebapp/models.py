"""
SQLAlchemy models for the Rage N Raze IT Asset Management system.
"""

import json
from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    """Application user, authenticated locally or synced from Active Directory."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    display_name = db.Column(db.String(250))
    email = db.Column(db.String(250))
    role = db.Column(db.String(20), nullable=False, default="viewer")  # admin | technician | viewer
    password_hash = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class Category(db.Model):
    """Asset category (e.g. Laptop, Operating System)."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    asset_type = db.Column(db.String(20), nullable=False)  # 'hardware' | 'software'
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Category {self.name} ({self.asset_type})>"


# ---------------------------------------------------------------------------
# Hardware Asset
# ---------------------------------------------------------------------------
class HardwareAsset(db.Model):
    """Physical / hardware asset record."""

    __tablename__ = "hardware_assets"

    id = db.Column(db.Integer, primary_key=True)
    asset_tag = db.Column(db.String(20), unique=True, nullable=False)  # HW-XXXXX
    name = db.Column(db.String(250), nullable=False)
    manufacturer = db.Column(db.String(250))
    model = db.Column(db.String(250))
    serial_number = db.Column(db.String(250))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    status = db.Column(db.String(30), nullable=False, default="In Stock")  # In Stock | Deployed | In Repair | Retired
    assigned_to = db.Column(db.String(250))
    purchase_date = db.Column(db.Date)
    warranty_expiry = db.Column(db.Date)
    location = db.Column(db.String(250))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.String(150))

    category = db.relationship("Category", backref="hardware_assets", lazy=True)

    def __repr__(self):
        return f"<HardwareAsset {self.asset_tag} – {self.name}>"


# ---------------------------------------------------------------------------
# Software Asset
# ---------------------------------------------------------------------------
class SoftwareAsset(db.Model):
    """Software licence / subscription record."""

    __tablename__ = "software_assets"

    id = db.Column(db.Integer, primary_key=True)
    asset_tag = db.Column(db.String(20), unique=True, nullable=False)  # SW-XXXXX
    name = db.Column(db.String(250), nullable=False)
    version = db.Column(db.String(100))
    vendor = db.Column(db.String(250))
    license_key = db.Column(db.String(500))
    license_type = db.Column(db.String(30))  # Per Seat | Per Device | Site License | Open Source | Subscription
    total_seats = db.Column(db.Integer)
    used_seats = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    status = db.Column(db.String(30), nullable=False, default="Active")  # Active | Expired | Retired
    assigned_to = db.Column(db.String(250))
    purchase_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.String(150))

    category = db.relationship("Category", backref="software_assets", lazy=True)

    def __repr__(self):
        return f"<SoftwareAsset {self.asset_tag} – {self.name}>"


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------
class AuditLog(db.Model):
    """Immutable audit trail for every mutating action."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # CREATE | UPDATE | DELETE
    entity_type = db.Column(db.String(30), nullable=False)  # hardware | software | category | user
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON string of changes
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type}#{self.entity_id} by {self.user}>"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def log_action(user: str, action: str, entity_type: str, entity_id: int, details: str | dict | None = None):
    """Create an AuditLog entry and flush it to the database.

    Args:
        user: Username of the person performing the action.
        action: One of 'CREATE', 'UPDATE', 'DELETE'.
        entity_type: One of 'hardware', 'software', 'category', 'user'.
        entity_id: Primary key of the affected entity.
        details: Free-form description or dict (auto-serialised to JSON).
    """
    if isinstance(details, dict):
        details = json.dumps(details)
    entry = AuditLog(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.session.add(entry)
    db.session.commit()
