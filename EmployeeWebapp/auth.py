"""
LDAP authentication and Flask-Login initialisation for Rage N Raze.
"""

import logging
import ssl

# Ensure MD4 hash algorithm is available for NTLM under Python 3.10+ / OpenSSL 3
from md4_patch import apply_md4_patch
apply_md4_patch()

from flask import current_app
from flask_login import LoginManager
from ldap3 import ALL, Connection, Server, NTLM, SIMPLE, Tls
from ldap3.core.exceptions import LDAPException

from models import User, db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LDAP authentication
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


def authenticate_ldap(username: str, password: str) -> dict | None:
    """Authenticate a user against Active Directory via LDAP.

    Supports:
      - Windows NTLM authentication (solves 'strongerAuthRequired' over port 389)
      - LDAPS (port 636) with certificate tolerance
      - Standard SIMPLE bind fallback
      - Local dev account fallback if ALLOW_LOCAL_DEV_LOGIN is enabled

    Returns a dict with keys ``username``, ``display_name``, ``email``, and
    ``role`` on success, or ``None`` on failure.
    """
    # Check local dev accounts first if enabled
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
    viewer_group = current_app.config["LDAP_VIEWER_GROUP"]

    # Support both "DOMAIN\username" and simple "username"
    clean_username = username.split("\\")[-1] if "\\" in username else username
    bind_dn = f"{ldap_domain}\\{clean_username}"

    is_ssl = ldap_server.lower().startswith("ldaps://") or ":636" in ldap_server
    tls_config = Tls(validate=ssl.CERT_NONE) if is_ssl else None

    conn = None
    server = Server(ldap_server, use_ssl=is_ssl, tls=tls_config, get_info=ALL)

    # 1. First attempt Windows NTLM authentication (solves 'strongerAuthRequired')
    try:
        conn = Connection(server, user=bind_dn, password=password, authentication=NTLM, auto_bind=True)
    except Exception as ntlm_err:
        logger.debug("NTLM bind attempt notice for %s: %s", clean_username, ntlm_err)

    # 2. Fall back to SIMPLE bind if NTLM was not accepted
    if conn is None:
        try:
            conn = Connection(server, user=bind_dn, password=password, authentication=SIMPLE, auto_bind=True)
        except LDAPException as exc:
            logger.error("LDAP bind failed for %s: %s", clean_username, exc)
            return None
        except Exception as exc:  # noqa: BLE001 – catch-all for network errors
            logger.error("LDAP connection error for %s: %s", clean_username, exc)
            return None

    try:
        # Search for the authenticated user's attributes
        search_filter = f"(sAMAccountName={clean_username})"
        conn.search(
            search_base=ldap_search_base,
            search_filter=search_filter,
            attributes=["displayName", "mail", "memberOf"],
        )

        # Fallback to searching the broader domain root if not in specific OU
        if not conn.entries and ldap_base_dn and ldap_base_dn != ldap_search_base:
            conn.search(
                search_base=ldap_base_dn,
                search_filter=search_filter,
                attributes=["displayName", "mail", "memberOf"],
            )

        if not conn.entries:
            # User authenticated successfully via bind, but search didn't find attributes
            logger.warning("LDAP user %s authenticated, but search returned no entry", clean_username)
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

        # Determine role from group membership
        member_of_raw = entry.memberOf.values if hasattr(entry, "memberOf") and entry.memberOf else []
        member_of = [str(g) for g in member_of_raw]

        role = "viewer"  # default
        for group_dn in member_of:
            group_dn_upper = group_dn.upper()
            if f"CN={admin_group}".upper() in group_dn_upper:
                role = "admin"
                break
            if f"CN={tech_group}".upper() in group_dn_upper:
                role = "technician"
                # Don't break — admin takes precedence if found later

        conn.unbind()

        return {
            "username": clean_username,
            "display_name": display_name,
            "email": email,
            "role": role,
        }

    except LDAPException as exc:
        logger.error("LDAP search error for %s: %s", clean_username, exc)
        try:
            conn.unbind()
        except Exception:  # noqa: BLE001
            pass
        return None


# ---------------------------------------------------------------------------
# Flask-Login initialisation
# ---------------------------------------------------------------------------
def init_login_manager(app):
    """Create and configure the Flask-Login ``LoginManager``.

    Returns the ``LoginManager`` instance (also attached to *app*).
    """
    login_manager = LoginManager()
    login_manager.login_view = "main.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return login_manager
