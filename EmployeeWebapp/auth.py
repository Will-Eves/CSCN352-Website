"""
Active Directory & LDAP authentication and Flask-Login initialisation for Rage N Raze.
"""

import logging
import os
import ssl

# Ensure MD4 hash algorithm is available for NTLM under Python 3.10+ / OpenSSL 3
from md4_patch import apply_md4_patch
apply_md4_patch()

from flask import current_app
from flask_login import LoginManager
from models import User, db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dev / Lab Demo Accounts
# ---------------------------------------------------------------------------
DEV_USERS = {
    "admin": {
        "password": "admin123",
        "display_name": "IT Administrator",
        "email": "admin@ragenraze.local",
        "role": "admin",
    },
    "tech": {
        "password": "tech123",
        "display_name": "IT Technician",
        "email": "technician@ragenraze.local",
        "role": "technician",
    },
    "viewer": {
        "password": "viewer123",
        "display_name": "Inventory Auditor",
        "email": "viewer@ragenraze.local",
        "role": "viewer",
    },
}


def authenticate_windows_native(domain: str, username: str, password: str, admin_group: str, tech_group: str) -> dict | None:
    """Authenticate directly using the Windows Operating System security provider (Advapi32.dll LogonUserW).

    Bypasses LDAP port 389/636 signing and SSL requirements on Windows Server 2025.
    """
    if os.name != "nt":
        return None

    try:
        import ctypes
        from ctypes import wintypes
        import subprocess

        LOGON32_LOGON_NETWORK = 3
        LOGON32_PROVIDER_DEFAULT = 0

        token = wintypes.HANDLE()
        advapi32 = ctypes.windll.advapi32
        kernel32 = ctypes.windll.kernel32

        clean_user = username.split("\\")[-1] if "\\" in username else username
        success = advapi32.LogonUserW(
            clean_user,
            domain.strip(),
            password,
            LOGON32_LOGON_NETWORK,
            LOGON32_PROVIDER_DEFAULT,
            ctypes.byref(token),
        )
        if not success:
            return None

        kernel32.CloseHandle(token)

        # Retrieve user display name and groups via Windows net user
        full_name = clean_user
        groups = []
        try:
            cmd = ["net", "user", clean_user, "/domain"]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            for line in out.splitlines():
                if line.startswith("Full Name"):
                    val = line.replace("Full Name", "").strip()
                    if val:
                        full_name = val
                if "Group Memberships" in line or "Group memberships" in line:
                    parts = line.split("*")[1:]
                    for p in parts:
                        clean_p = p.strip()
                        if clean_p and clean_p.lower() != "none":
                            groups.append(clean_p)
        except Exception:
            pass

        # Determine role from group membership
        role = "viewer"
        admin_targets = [admin_group.upper(), "DOMAIN ADMINS", "ADMINISTRATORS", "CLIENT SERVICES"]
        tech_targets = [tech_group.upper(), "HELPDESK"]

        for g in groups:
            g_up = g.upper()
            if any(target in g_up for target in admin_targets):
                role = "admin"
                break
            if any(target in g_up for target in tech_targets):
                role = "technician"

        return {
            "username": clean_user,
            "display_name": full_name,
            "email": "",
            "role": role,
        }
    except Exception as e:
        logger.error("Windows native authentication error: %s", e)
        return None


def authenticate_ldap(username: str, password: str) -> dict | None:
    """Authenticate a user against Active Directory.

    Checks:
      1. Local dev fallback accounts (if ALLOW_LOCAL_DEV_LOGIN is enabled)
      2. Windows Native LogonUserW (bypasses port 389/636 signing on Windows Server)
      3. Standard LDAP3 bind (NTLM / SIMPLE / LDAPS)
    """
    # 1. Check local dev accounts first if enabled
    if current_app.config.get("ALLOW_LOCAL_DEV_LOGIN", False):
        user_key = username.lower().strip()
        if user_key in DEV_USERS and DEV_USERS[user_key]["password"] == password:
            data = DEV_USERS[user_key]
            return {
                "username": username,
                "display_name": data["display_name"],
                "email": data["email"],
                "role": data["role"],
            }

    ldap_server = current_app.config["LDAP_SERVER"]
    ldap_domain = current_app.config["LDAP_DOMAIN"]
    ldap_base_dn = current_app.config["LDAP_BASE_DN"]
    ldap_search_base = current_app.config["LDAP_USER_SEARCH_BASE"]
    admin_group = current_app.config["LDAP_ADMIN_GROUP"]
    tech_group = current_app.config["LDAP_TECH_GROUP"]

    clean_username = username.split("\\")[-1] if "\\" in username else username

    # 2. Try native Windows Domain Logon if running on Windows Server
    if os.name == "nt":
        native_user = authenticate_windows_native(ldap_domain, clean_username, password, admin_group, tech_group)
        if native_user is not None:
            return native_user

    # 3. LDAP fallback via ldap3
    try:
        from ldap3 import ALL, Connection, Server, NTLM, SIMPLE, Tls
        from ldap3.core.exceptions import LDAPException
    except ImportError:
        return None

    bind_dn = f"{ldap_domain}\\{clean_username}"
    is_ssl = ldap_server.lower().startswith("ldaps://") or ":636" in ldap_server
    tls_config = Tls(validate=ssl.CERT_NONE) if is_ssl else None

    conn = None
    server = Server(ldap_server, use_ssl=is_ssl, tls=tls_config, get_info=ALL)

    try:
        conn = Connection(server, user=bind_dn, password=password, authentication=NTLM, auto_bind=True)
    except Exception:
        pass

    if conn is None:
        try:
            conn = Connection(server, user=bind_dn, password=password, authentication=SIMPLE, auto_bind=True)
        except Exception as exc:
            logger.error("LDAP bind failed for %s: %s", clean_username, exc)
            return None

    try:
        search_filter = f"(sAMAccountName={clean_username})"
        conn.search(
            search_base=ldap_search_base,
            search_filter=search_filter,
            attributes=["displayName", "mail", "memberOf"],
        )

        if not conn.entries and ldap_base_dn and ldap_base_dn != ldap_search_base:
            conn.search(
                search_base=ldap_base_dn,
                search_filter=search_filter,
                attributes=["displayName", "mail", "memberOf"],
            )

        if not conn.entries:
            conn.unbind()
            return {
                "username": clean_username,
                "display_name": clean_username,
                "email": "",
                "role": "viewer",
            }

        entry = conn.entries[0]
        display_name = str(entry.displayName) if hasattr(entry, "displayName") and entry.displayName else clean_username
        email = str(entry.mail) if hasattr(entry, "mail") and entry.mail else ""

        member_of_raw = entry.memberOf.values if hasattr(entry, "memberOf") and entry.memberOf else []
        member_of = [str(g) for g in member_of_raw]

        role = "viewer"
        for group_dn in member_of:
            group_dn_upper = group_dn.upper()
            if f"CN={admin_group}".upper() in group_dn_upper or "DOMAIN ADMINS" in group_dn_upper:
                role = "admin"
                break
            if f"CN={tech_group}".upper() in group_dn_upper or "HELPDESK" in group_dn_upper:
                role = "technician"

        conn.unbind()

        return {
            "username": clean_username,
            "display_name": display_name,
            "email": email,
            "role": role,
        }

    except Exception as exc:
        logger.error("LDAP search error for %s: %s", clean_username, exc)
        return None


# ---------------------------------------------------------------------------
# Flask-Login initialisation
# ---------------------------------------------------------------------------
def init_login_manager(app):
    """Create and configure the Flask-Login ``LoginManager``."""
    login_manager = LoginManager()
    login_manager.login_view = "main.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return login_manager
