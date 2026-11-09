"""
Asset routes — hardware and software CRUD.
"""

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import AuditLog, Category, HardwareAsset, SoftwareAsset, db, log_action
from routes.decorators import role_required

assets = Blueprint("assets", __name__)


# ═══════════════════════════════════════════════════════════════════════════
# HARDWARE
# ═══════════════════════════════════════════════════════════════════════════

@assets.route("/hardware")
@login_required
def hardware_list():
    """List hardware assets with optional search and filters."""
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "", type=str).strip()
    status_filter = request.args.get("status", "", type=str).strip()
    category_filter = request.args.get("category", "", type=int)

    query = HardwareAsset.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            HardwareAsset.name.ilike(like)
            | HardwareAsset.asset_tag.ilike(like)
            | HardwareAsset.serial_number.ilike(like)
            | HardwareAsset.manufacturer.ilike(like)
            | HardwareAsset.model.ilike(like)
            | HardwareAsset.assigned_to.ilike(like)
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    if category_filter:
        query = query.filter_by(category_id=category_filter)

    query = query.order_by(HardwareAsset.created_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)

    categories = Category.query.filter_by(asset_type="hardware", is_active=True).all()

    return render_template(
        "hardware.html",
        assets=pagination,
        pagination=pagination,
        categories=categories,
        q=q,
        status_filter=status_filter,
        category_filter=category_filter,
    )


@assets.route("/hardware/<int:asset_id>")
@login_required
def hardware_detail(asset_id):
    """Show details for a single hardware asset."""
    asset = HardwareAsset.query.get_or_404(asset_id)
    categories = Category.query.filter_by(asset_type="hardware", is_active=True).all()
    logs = (
        AuditLog.query.filter_by(entity_type="hardware", entity_id=asset.id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return render_template(
        "asset_detail.html",
        asset=asset,
        asset_type="hardware",
        categories=categories,
        logs=logs,
    )


@assets.route("/hardware/add", methods=["POST"])
@login_required
@role_required("technician", "admin")
def hardware_add():
    """Create a new hardware asset."""
    # Generate next asset tag
    max_id = db.session.query(db.func.max(HardwareAsset.id)).scalar() or 0
    asset_tag = f"HW-{max_id + 1:05d}"

    purchase_date = _parse_date(request.form.get("purchase_date"))
    warranty_expiry = _parse_date(request.form.get("warranty_expiry"))

    asset = HardwareAsset(
        asset_tag=asset_tag,
        name=request.form.get("name", "").strip(),
        manufacturer=request.form.get("manufacturer", "").strip(),
        model=request.form.get("model", "").strip(),
        serial_number=request.form.get("serial_number", "").strip(),
        category_id=request.form.get("category_id", type=int),
        status=request.form.get("status", "In Stock"),
        assigned_to=request.form.get("assigned_to", "").strip(),
        purchase_date=purchase_date,
        warranty_expiry=warranty_expiry,
        location=request.form.get("location", "").strip(),
        notes=request.form.get("notes", "").strip(),
        created_by=current_user.username,
    )
    db.session.add(asset)
    db.session.commit()

    log_action(current_user.username, "CREATE", "hardware", asset.id, {"asset_tag": asset.asset_tag, "name": asset.name})
    flash(f"Hardware asset {asset.asset_tag} created successfully.", "success")
    return redirect(url_for("assets.hardware_list"))


@assets.route("/hardware/<int:asset_id>/edit", methods=["POST"])
@login_required
@role_required("technician", "admin")
def hardware_edit(asset_id):
    """Update an existing hardware asset."""
    asset = HardwareAsset.query.get_or_404(asset_id)

    changes = {}
    for field in ("name", "manufacturer", "model", "serial_number", "status", "assigned_to", "location", "notes"):
        new_val = request.form.get(field, "").strip()
        old_val = getattr(asset, field) or ""
        if new_val != old_val:
            changes[field] = {"old": old_val, "new": new_val}
            setattr(asset, field, new_val)

    new_cat = request.form.get("category_id", type=int)
    if new_cat and new_cat != asset.category_id:
        changes["category_id"] = {"old": asset.category_id, "new": new_cat}
        asset.category_id = new_cat

    purchase_date = _parse_date(request.form.get("purchase_date"))
    if purchase_date != asset.purchase_date:
        changes["purchase_date"] = {"old": str(asset.purchase_date), "new": str(purchase_date)}
        asset.purchase_date = purchase_date

    warranty_expiry = _parse_date(request.form.get("warranty_expiry"))
    if warranty_expiry != asset.warranty_expiry:
        changes["warranty_expiry"] = {"old": str(asset.warranty_expiry), "new": str(warranty_expiry)}
        asset.warranty_expiry = warranty_expiry

    db.session.commit()
    log_action(current_user.username, "UPDATE", "hardware", asset.id, changes)
    flash(f"Hardware asset {asset.asset_tag} updated.", "success")
    return redirect(url_for("assets.hardware_detail", asset_id=asset.id))


@assets.route("/hardware/<int:asset_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def hardware_delete(asset_id):
    """Delete a hardware asset (admin only)."""
    asset = HardwareAsset.query.get_or_404(asset_id)
    tag = asset.asset_tag
    db.session.delete(asset)
    db.session.commit()

    log_action(current_user.username, "DELETE", "hardware", asset_id, {"asset_tag": tag})
    flash(f"Hardware asset {tag} deleted.", "success")
    return redirect(url_for("assets.hardware_list"))


# ═══════════════════════════════════════════════════════════════════════════
# SOFTWARE
# ═══════════════════════════════════════════════════════════════════════════

@assets.route("/software")
@login_required
def software_list():
    """List software assets with optional search and filters."""
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "", type=str).strip()
    status_filter = request.args.get("status", "", type=str).strip()
    category_filter = request.args.get("category", "", type=int)

    query = SoftwareAsset.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            SoftwareAsset.name.ilike(like)
            | SoftwareAsset.asset_tag.ilike(like)
            | SoftwareAsset.vendor.ilike(like)
            | SoftwareAsset.license_key.ilike(like)
            | SoftwareAsset.assigned_to.ilike(like)
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    if category_filter:
        query = query.filter_by(category_id=category_filter)

    query = query.order_by(SoftwareAsset.created_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)

    categories = Category.query.filter_by(asset_type="software", is_active=True).all()

    return render_template(
        "software.html",
        assets=pagination,
        pagination=pagination,
        categories=categories,
        q=q,
        status_filter=status_filter,
        category_filter=category_filter,
    )


@assets.route("/software/<int:asset_id>")
@login_required
def software_detail(asset_id):
    """Show details for a single software asset."""
    asset = SoftwareAsset.query.get_or_404(asset_id)
    categories = Category.query.filter_by(asset_type="software", is_active=True).all()
    logs = (
        AuditLog.query.filter_by(entity_type="software", entity_id=asset.id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return render_template(
        "asset_detail.html",
        asset=asset,
        asset_type="software",
        categories=categories,
        logs=logs,
    )


@assets.route("/software/add", methods=["POST"])
@login_required
@role_required("technician", "admin")
def software_add():
    """Create a new software asset."""
    max_id = db.session.query(db.func.max(SoftwareAsset.id)).scalar() or 0
    asset_tag = f"SW-{max_id + 1:05d}"

    purchase_date = _parse_date(request.form.get("purchase_date"))
    expiry_date = _parse_date(request.form.get("expiry_date"))

    asset = SoftwareAsset(
        asset_tag=asset_tag,
        name=request.form.get("name", "").strip(),
        version=request.form.get("version", "").strip(),
        vendor=request.form.get("vendor", "").strip(),
        license_key=request.form.get("license_key", "").strip(),
        license_type=request.form.get("license_type", ""),
        total_seats=request.form.get("total_seats", type=int),
        used_seats=request.form.get("used_seats", 0, type=int),
        category_id=request.form.get("category_id", type=int),
        status=request.form.get("status", "Active"),
        assigned_to=request.form.get("assigned_to", "").strip(),
        purchase_date=purchase_date,
        expiry_date=expiry_date,
        notes=request.form.get("notes", "").strip(),
        created_by=current_user.username,
    )
    db.session.add(asset)
    db.session.commit()

    log_action(current_user.username, "CREATE", "software", asset.id, {"asset_tag": asset.asset_tag, "name": asset.name})
    flash(f"Software asset {asset.asset_tag} created successfully.", "success")
    return redirect(url_for("assets.software_list"))


@assets.route("/software/<int:asset_id>/edit", methods=["POST"])
@login_required
@role_required("technician", "admin")
def software_edit(asset_id):
    """Update an existing software asset."""
    asset = SoftwareAsset.query.get_or_404(asset_id)

    changes = {}
    for field in ("name", "version", "vendor", "license_key", "license_type", "status", "assigned_to", "notes"):
        new_val = request.form.get(field, "").strip()
        old_val = getattr(asset, field) or ""
        if new_val != old_val:
            changes[field] = {"old": old_val, "new": new_val}
            setattr(asset, field, new_val)

    for int_field in ("total_seats", "used_seats"):
        new_val = request.form.get(int_field, type=int)
        old_val = getattr(asset, int_field)
        if new_val is not None and new_val != old_val:
            changes[int_field] = {"old": old_val, "new": new_val}
            setattr(asset, int_field, new_val)

    new_cat = request.form.get("category_id", type=int)
    if new_cat and new_cat != asset.category_id:
        changes["category_id"] = {"old": asset.category_id, "new": new_cat}
        asset.category_id = new_cat

    purchase_date = _parse_date(request.form.get("purchase_date"))
    if purchase_date != asset.purchase_date:
        changes["purchase_date"] = {"old": str(asset.purchase_date), "new": str(purchase_date)}
        asset.purchase_date = purchase_date

    expiry_date = _parse_date(request.form.get("expiry_date"))
    if expiry_date != asset.expiry_date:
        changes["expiry_date"] = {"old": str(asset.expiry_date), "new": str(expiry_date)}
        asset.expiry_date = expiry_date

    db.session.commit()
    log_action(current_user.username, "UPDATE", "software", asset.id, changes)
    flash(f"Software asset {asset.asset_tag} updated.", "success")
    return redirect(url_for("assets.software_detail", asset_id=asset.id))


@assets.route("/software/<int:asset_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def software_delete(asset_id):
    """Delete a software asset (admin only)."""
    asset = SoftwareAsset.query.get_or_404(asset_id)
    tag = asset.asset_tag
    db.session.delete(asset)
    db.session.commit()

    log_action(current_user.username, "DELETE", "software", asset_id, {"asset_tag": tag})
    flash(f"Software asset {tag} deleted.", "success")
    return redirect(url_for("assets.software_list"))


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _parse_date(value: str | None):
    """Parse a date string (YYYY-MM-DD) from a form field; return None on failure."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None
