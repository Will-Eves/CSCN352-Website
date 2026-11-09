"""
Category management routes (admin only).
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import Category, db, log_action
from routes.decorators import role_required

categories = Blueprint("categories", __name__)


@categories.route("/categories")
@login_required
@role_required("admin")
def category_list():
    """List all asset categories (hardware and software)."""
    hardware_categories = (
        Category.query.filter_by(asset_type="hardware")
        .order_by(Category.name)
        .all()
    )
    software_categories = (
        Category.query.filter_by(asset_type="software")
        .order_by(Category.name)
        .all()
    )
    all_categories = Category.query.order_by(Category.asset_type, Category.name).all()
    return render_template(
        "categories.html",
        hardware_categories=hardware_categories,
        software_categories=software_categories,
        categories=all_categories,
    )


@categories.route("/categories/add", methods=["POST"])
@login_required
@role_required("admin")
def category_add():
    """Create a new category."""
    name = request.form.get("name", "").strip()
    asset_type = (request.form.get("asset_type") or request.form.get("type") or "").strip()
    description = request.form.get("description", "").strip()

    if not name or asset_type not in ("hardware", "software"):
        flash("Category name and a valid asset type are required.", "warning")
        return redirect(url_for("categories.category_list"))

    cat = Category(name=name, asset_type=asset_type, description=description)
    db.session.add(cat)
    db.session.commit()

    log_action(current_user.username, "CREATE", "category", cat.id, {"name": name, "asset_type": asset_type})
    flash(f"Category '{name}' created.", "success")
    return redirect(url_for("categories.category_list"))


@categories.route("/categories/<int:cat_id>/edit", methods=["POST"])
@login_required
@role_required("admin")
def category_edit(cat_id):
    """Update an existing category."""
    cat = Category.query.get_or_404(cat_id)

    changes = {}
    for field in ("name", "asset_type", "description"):
        new_val = request.form.get(field, "").strip()
        old_val = getattr(cat, field) or ""
        if new_val and new_val != old_val:
            changes[field] = {"old": old_val, "new": new_val}
            setattr(cat, field, new_val)

    db.session.commit()
    log_action(current_user.username, "UPDATE", "category", cat.id, changes)
    flash(f"Category '{cat.name}' updated.", "success")
    return redirect(url_for("categories.category_list"))


@categories.route("/categories/<int:cat_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def category_toggle(cat_id):
    """Toggle a category's active status."""
    cat = Category.query.get_or_404(cat_id)
    cat.is_active = not cat.is_active
    db.session.commit()

    status_str = "activated" if cat.is_active else "deactivated"
    log_action(current_user.username, "UPDATE", "category", cat.id, {"is_active": cat.is_active})
    flash(f"Category '{cat.name}' has been {status_str}.", "success")
    return redirect(url_for("categories.category_list"))


@categories.route("/categories/<int:cat_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def category_delete(cat_id):
    """Soft-delete a category (set is_active = False)."""
    cat = Category.query.get_or_404(cat_id)
    cat.is_active = False
    db.session.commit()

    log_action(current_user.username, "DELETE", "category", cat.id, {"name": cat.name, "soft_delete": True})
    flash(f"Category '{cat.name}' has been deactivated.", "success")
    return redirect(url_for("categories.category_list"))
