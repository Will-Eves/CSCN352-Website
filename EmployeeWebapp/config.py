"""
Configuration for the Rage N Raze Employee IT Asset Management Webapp.
"""

import os


class Config:
    """Application configuration loaded from environment variables with sensible defaults."""

    # Flask core
    SECRET_KEY = os.environ.get("SECRET_KEY", "rnr-asset-mgmt-change-me-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI",
        "sqlite:///"
        + os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "instance", "assets.db"
        ),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LDAP / Active Directory
    LDAP_SERVER = os.environ.get("LDAP_SERVER", "ldap://dc.ragenraze.local")
    LDAP_BASE_DN = os.environ.get("LDAP_BASE_DN", "DC=ragenraze,DC=local")
    LDAP_DOMAIN = os.environ.get("LDAP_DOMAIN", "RAGENRAZE")
    LDAP_USER_SEARCH_BASE = os.environ.get(
        "LDAP_USER_SEARCH_BASE", "OU=Users,DC=ragenraze,DC=local"
    )

    # LDAP group-to-role mapping
    LDAP_ADMIN_GROUP = os.environ.get("LDAP_ADMIN_GROUP", "IT-Admins")
    LDAP_TECH_GROUP = os.environ.get("LDAP_TECH_GROUP", "IT-Technicians")
    LDAP_VIEWER_GROUP = os.environ.get("LDAP_VIEWER_GROUP", "IT-Viewers")

    # Local fallback / dev credentials for testing without an active domain controller
    ALLOW_LOCAL_DEV_LOGIN = os.environ.get("ALLOW_LOCAL_DEV_LOGIN", "true").lower() in ("true", "1", "yes")
