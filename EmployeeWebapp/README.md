# Rage N Raze — IT Asset Management Webapp

A dark-themed, Ivanti-style IT asset management web application built with Flask for **Rage N Raze**, a demolition company. Track hardware and software assets, manage asset categories, and control access with Active Directory / LDAP authentication and 3-tier role-based access control.

---

## Theming & Design System

The application strictly follows the brand guidelines defined in the repository root:

| Token | Hex Value | Purpose |
|---|---|---|
| `--ink` | `#111214` | Body background, inputs, dark canvas |
| `--panel` | `#1b1c1e` | Sidebar, cards, modal content, table header |
| `--yellow` | `#ffc400` | Primary accent, CTA buttons, active links, badges |
| `--paper` | `#f5f3ed` | Primary text and headings |
| `--muted` | `#b8b8b5` | Secondary text, captions, timestamps |
| `--line` | `#393a3c` | Borders, table row dividers, input outlines |

- **Title Font:** `Barlow Condensed` (Google Fonts)
- **Paragraph Font:** `Arial`

---

## Features

- **Ivanti-Style Asset Management:**
  - Hardware inventory with auto-generated tags (`HW-00001`, `HW-00002`, ...)
  - Software licensing inventory with auto-generated tags (`SW-00001`, `SW-00002`, ...)
  - Seat allocation tracking (`used_seats` / `total_seats`)
  - Filter by status and category, real-time debounced search, sortable columns, and pagination
  - Single-asset detail view with inline edit mode and deletion protection
- **Active Directory / LDAP Authentication:**
  - Directly binds to Windows Active Directory domain controller
  - Queries user attributes (`displayName`, `mail`) and AD group memberships (`memberOf`)
  - Automatic role mapping based on AD security groups
  - Local dev fallback mode for testing/grading without an Active Directory domain controller
- **Admin Category Management:**
  - Admins can add new hardware and software categories
  - Edit existing category names and descriptions
  - Soft-delete or toggle active/inactive status
- **Role-Based Access Control (RBAC):**
  - **Viewer:** Read-only access to inventory and dashboards
  - **Technician:** Read-only + add and edit hardware and software assets
  - **Admin:** Full privileges (add, edit, delete assets, manage categories, promote/demote user roles)
- **Comprehensive Audit Trail:**
  - Every mutating action (`CREATE`, `UPDATE`, `DELETE`) is recorded with user, timestamp, and JSON delta

---

## Quick Start

### 1. Install Dependencies

```bash
cd EmployeeWebapp
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The application runs locally at `http://127.0.0.1:5000`. On first launch, SQLite (`instance/assets.db`) is automatically initialized and seeded with default categories.

---

## LDAP & Active Directory Configuration

Configure your domain controller by setting the environment variables below (or edit `config.py`):

| Environment Variable | Default Value | Description |
|---|---|---|
| `LDAP_SERVER` | `ldap://dc.ragenraze.local` | URI of the Windows Domain Controller |
| `LDAP_DOMAIN` | `RAGENRAZE` | NetBIOS domain name for bind (`DOMAIN\username`) |
| `LDAP_BASE_DN` | `DC=ragenraze,DC=local` | Base DN for user and group searches |
| `LDAP_USER_SEARCH_BASE` | `OU=Users,DC=ragenraze,DC=local` | User search base OU |
| `LDAP_ADMIN_GROUP` | `IT-Admins` | AD security group mapped to **Admin** role |
| `LDAP_TECH_GROUP` | `IT-Technicians` | AD security group mapped to **Technician** role |
| `LDAP_VIEWER_GROUP` | `IT-Viewers` | AD security group mapped to **Viewer** role |
| `ALLOW_LOCAL_DEV_LOGIN` | `true` | Allows local demo login without an active DC |
| `SECRET_KEY` | `rnr-asset-mgmt-change-me` | Flask session secret key |
| `DATABASE_URI` | `sqlite:///instance/assets.db` | SQLAlchemy database connection URI |

### Built-in Test Accounts (Local Dev / Lab Testing)

When `ALLOW_LOCAL_DEV_LOGIN=true`, you can test all 3 permission levels without needing an active Windows Server:

| Username | Password | Role | Access Level |
|---|---|---|---|
| `admin` | `admin123` | **Admin** | Full access + Categories + User management |
| `tech` | `tech123` | **Technician** | View, Add, and Edit assets |
| `viewer` | `viewer123` | **Viewer** | View-only access |

---

## Running the Automated Test Suite

A comprehensive test suite is included in `test_app.py`:

```bash
python test_app.py
```

---

## Project Structure

```
EmployeeWebapp/
├── app.py                  # Flask application factory, DB init & category seeding
├── auth.py                 # LDAP Active Directory auth & Flask-Login manager
├── config.py               # Environment configuration
├── models.py               # SQLAlchemy ORM models (User, Asset, Category, AuditLog)
├── requirements.txt        # Python package dependencies
├── test_app.py             # Automated unit and integration test suite
├── routes/
│   ├── __init__.py
│   ├── admin.py            # User management & role assignment (/admin)
│   ├── assets.py           # Hardware & software CRUD, search, filter (/hardware, /software)
│   ├── categories.py       # Category creation, editing & toggles (/categories)
│   ├── decorators.py       # @role_required RBAC decorator
│   └── main.py             # Login, logout, dashboard metrics & activity log
├── static/
│   ├── css/
│   │   └── style.css       # Complete dark-theme stylesheet
│   └── js/
│       └── app.js          # Modals, client sort, debounced search, validations
└── templates/
    ├── base.html           # Master layout with responsive sidebar
    ├── login.html          # Domain login page
    ├── dashboard.html      # KPI widgets, status breakdown & audit table
    ├── hardware.html       # Hardware table, add modal, pagination
    ├── software.html       # Software table, license seats, add modal
    ├── asset_detail.html   # Detailed asset view, edit mode, delete, history
    ├── categories.html     # Admin category management (hardware + software)
    └── admin.html          # Admin user role assignment & active status toggle
```
