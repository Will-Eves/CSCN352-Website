"""
Automated end-to-end tests for the Rage N Raze Employee IT Asset Management Webapp.
"""

import sys
import unittest
from datetime import date
from flask import url_for
from app import create_app
from models import db, User, Category, HardwareAsset, SoftwareAsset, AuditLog


class AssetManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update({
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "ALLOW_LOCAL_DEV_LOGIN": True,
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            from app import _seed_default_categories
            _seed_default_categories()

    def login(self, username, password):
        return self.client.post("/login", data={
            "username": username,
            "password": password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    def test_default_categories_seeded(self):
        with self.app.app_context():
            hw_cats = Category.query.filter_by(asset_type="hardware").all()
            sw_cats = Category.query.filter_by(asset_type="software").all()
            self.assertGreaterEqual(len(hw_cats), 8)
            self.assertGreaterEqual(len(sw_cats), 7)
            names = [c.name for c in hw_cats]
            self.assertIn("Desktop", names)
            self.assertIn("Laptop", names)

    def test_login_and_roles(self):
        # 1. Failed login
        resp = self.login("admin", "wrongpass")
        self.assertIn(b"Invalid credentials", resp.data)

        # 2. Login as admin
        resp = self.login("admin", "admin123")
        self.assertIn(b"Welcome back", resp.data)
        self.assertIn(b"Dashboard", resp.data)
        with self.app.app_context():
            u = User.query.filter_by(username="admin").first()
            self.assertIsNotNone(u)
            self.assertEqual(u.role, "admin")

        self.logout()

        # 3. Login as technician
        resp = self.login("tech", "tech123")
        self.assertIn(b"Welcome back", resp.data)
        with self.app.app_context():
            u = User.query.filter_by(username="tech").first()
            self.assertEqual(u.role, "technician")

        self.logout()

        # 4. Login as viewer
        resp = self.login("viewer", "viewer123")
        self.assertIn(b"Welcome back", resp.data)
        with self.app.app_context():
            u = User.query.filter_by(username="viewer").first()
            self.assertEqual(u.role, "viewer")

    def test_rbac_restrictions(self):
        # Viewer should NOT access categories page or admin page
        self.login("viewer", "viewer123")
        resp = self.client.get("/categories", follow_redirects=True)
        self.assertIn(b"You do not have permission", resp.data)

        resp = self.client.get("/admin/", follow_redirects=True)
        self.assertIn(b"You do not have permission", resp.data)

        # Viewer should NOT be able to add hardware
        resp = self.client.post("/hardware/add", data={"name": "Illegal PC"}, follow_redirects=True)
        self.assertIn(b"You do not have permission", resp.data)

        self.logout()

        # Technician can access hardware/software but NOT categories or admin
        self.login("tech", "tech123")
        resp = self.client.get("/categories", follow_redirects=True)
        self.assertIn(b"You do not have permission", resp.data)

        resp = self.client.get("/admin/", follow_redirects=True)
        self.assertIn(b"You do not have permission", resp.data)

        # Technician CAN add hardware
        resp = self.client.post("/hardware/add", data={
            "name": "Dell Precision 5570",
            "manufacturer": "Dell",
            "model": "Precision 5570",
            "serial_number": "SN-998877",
            "category_id": "2",
            "status": "In Stock",
            "assigned_to": "Jane Smith",
            "location": "HQ Demolition Office",
            "notes": "Workstation for blasting lead",
        }, follow_redirects=True)
        self.assertIn(b"created successfully", resp.data)
        self.assertIn(b"HW-00001", resp.data)

        # Technician cannot delete hardware
        with self.app.app_context():
            hw = HardwareAsset.query.first()
            hw_id = hw.id
        resp = self.client.post(f"/hardware/{hw_id}/delete", follow_redirects=True)
        self.assertIn(b"You do not have permission", resp.data)

        self.logout()

    def test_admin_full_workflow(self):
        self.login("admin", "admin123")

        # 1. Add Hardware
        resp = self.client.post("/hardware/add", data={
            "name": "HP ZBook Fury 16 G9",
            "manufacturer": "HP",
            "model": "ZBook Fury",
            "serial_number": "CZ12345678",
            "category_id": "2",
            "status": "Deployed",
            "assigned_to": "Bob Blaster",
            "location": "Site Site-A",
            "notes": "Rugged laptop for on-site surveying",
        }, follow_redirects=True)
        self.assertIn(b"HW-00001", resp.data)

        # 2. Add Software
        resp = self.client.post("/software/add", data={
            "name": "AutoCAD 2026",
            "version": "2026.1",
            "vendor": "Autodesk",
            "license_key": "ACAD-9921-X99",
            "license_type": "Per Seat",
            "total_seats": "10",
            "used_seats": "3",
            "status": "Active",
            "assigned_to": "Engineering Team",
            "notes": "Structural blueprints demolition plan",
        }, follow_redirects=True)
        self.assertIn(b"SW-00001", resp.data)

        # 3. View detail pages
        with self.app.app_context():
            hw = HardwareAsset.query.first()
            sw = SoftwareAsset.query.first()
            hw_id = hw.id
            sw_id = sw.id

        resp = self.client.get(f"/hardware/{hw_id}")
        self.assertIn(b"HP ZBook Fury 16 G9", resp.data)
        self.assertIn(b"Audit Trail", resp.data)

        resp = self.client.get(f"/software/{sw_id}")
        self.assertIn(b"AutoCAD 2026", resp.data)
        self.assertIn(b"Audit Trail", resp.data)

        # 4. Edit Hardware
        resp = self.client.post(f"/hardware/{hw_id}/edit", data={
            "name": "HP ZBook Fury 16 G9 (Upgraded)",
            "manufacturer": "HP",
            "model": "ZBook Fury",
            "serial_number": "CZ12345678",
            "category_id": "2",
            "status": "In Repair",
            "assigned_to": "Bob Blaster",
            "location": "IT Repair Depot",
            "notes": "Replaced trackpad",
        }, follow_redirects=True)
        self.assertIn(b"HP ZBook Fury 16 G9 (Upgraded)", resp.data)
        self.assertIn(b"In Repair", resp.data)

        # 5. Manage Categories (Admin Only)
        resp = self.client.get("/categories")
        self.assertIn(b"Manage Categories", resp.data)

        resp = self.client.post("/categories/add", data={
            "name": "Explosives Telemetry Devices",
            "asset_type": "hardware",
            "description": "Sensors and detonator logging units",
        }, follow_redirects=True)
        self.assertIn(b"Explosives Telemetry Devices", resp.data)

        with self.app.app_context():
            new_cat = Category.query.filter_by(name="Explosives Telemetry Devices").first()
            cat_id = new_cat.id

        # Toggle category active state
        resp = self.client.post(f"/categories/{cat_id}/toggle", follow_redirects=True)
        self.assertIn(b"deactivated", resp.data)

        # 6. Admin Panel (User Management)
        resp = self.client.get("/admin/")
        self.assertIn(b"User Management", resp.data)

        # 7. Audit log verification
        with self.app.app_context():
            logs = AuditLog.query.all()
            self.assertGreater(len(logs), 0)
            actions = [log.action for log in logs]
            self.assertIn("CREATE", actions)
            self.assertIn("UPDATE", actions)

        # 8. Delete asset
        resp = self.client.post(f"/hardware/{hw_id}/delete", follow_redirects=True)
        self.assertIn(b"deleted", resp.data)
        with self.app.app_context():
            self.assertIsNone(db.session.get(HardwareAsset, hw_id))


if __name__ == "__main__":
    unittest.main()
