"""
Rage N Raze — LDAP & Active Directory Diagnostic Tool
=====================================================
Run this script directly in PowerShell/CMD on your server to troubleshoot
Windows Domain & Active Directory connectivity, logins, and role mapping.
"""

import sys
import os
import socket
import ssl
import argparse
import getpass
import subprocess
import ctypes
from ctypes import wintypes

# Add current dir to path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Apply MD4 patch for Python 3.10+ / OpenSSL 3 environments before importing ldap3
from md4_patch import apply_md4_patch
apply_md4_patch()

try:
    from ldap3 import Server, Connection, ALL, SUBTREE, NTLM, SIMPLE, Tls
    from ldap3.core.exceptions import LDAPException, LDAPSocketOpenError, LDAPBindError
except ImportError:
    pass


def test_windows_native_logon(domain: str, username: str, password: str, admin_grp: str, tech_grp: str):
    """Test authentication directly through Windows LSA (Advapi32.dll LogonUserW).

    This uses the native Windows Operating System security channel, completely bypassing
    LDAP port 389 signing and SSL requirements.
    """
    print(f"\n[*] Testing Native Windows Domain Logon (Advapi32.dll LogonUserW) ...")
    LOGON32_LOGON_NETWORK = 3
    LOGON32_PROVIDER_DEFAULT = 0

    token = wintypes.HANDLE()
    advapi32 = ctypes.windll.advapi32
    kernel32 = ctypes.windll.kernel32

    clean_user = username.split("\\")[-1] if "\\" in username else username
    clean_domain = domain.strip()

    success = advapi32.LogonUserW(
        clean_user,
        clean_domain,
        password,
        LOGON32_LOGON_NETWORK,
        LOGON32_PROVIDER_DEFAULT,
        ctypes.byref(token),
    )

    if not success:
        err = ctypes.GetLastError()
        print(f"  [FAIL] Windows Native Logon Failed. Error code: {err}")
        if err == 1326:
            print("  --> HINT (1326): Invalid username or password.")
        elif err == 1327:
            print("  --> HINT (1327): User account restriction (e.g. blank password).")
        elif err == 1909:
            print("  --> HINT (1909): Account is locked out.")
        return False

    kernel32.CloseHandle(token)
    print(f"  [OK] Windows Native Logon SUCCESSFUL for '{clean_domain}\\{clean_user}'!")

    # Query groups using Windows net user
    print(f"\n[*] Checking Active Directory Group Membership via Windows ...")
    groups = []
    full_name = clean_user
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
    except Exception as e:
        print(f"  [INFO] Note querying net user: {e}")

    print(f"       Display Name: {full_name}")
    print(f"       Groups Found ({len(groups)}):")
    for g in groups:
        print(f"         - {g}")

    # Role evaluation
    role = "viewer"
    admin_targets = [admin_grp.upper(), "DOMAIN ADMINS", "ADMINISTRATORS"]
    tech_targets = [tech_grp.upper()]

    for g in groups:
        g_up = g.upper()
        if any(target in g_up for target in admin_targets):
            role = "admin"
            break
        if any(target in g_up for target in tech_targets):
            role = "technician"

    print(f"\n  ==================================================")
    print(f"  RESULT: User '{clean_user}' maps to role: [{role.upper()}]")
    print(f"  ==================================================")
    return True


def parse_host_port(server_uri: str):
    uri = server_uri.replace("ldap://", "").replace("ldaps://", "")
    if ":" in uri:
        host, port = uri.split(":", 1)
        return host, int(port)
    port = 636 if server_uri.startswith("ldaps://") else 389
    return uri, port


def main():
    parser = argparse.ArgumentParser(description="Test and diagnose Active Directory connectivity.")
    parser.add_argument("--server", default=Config.LDAP_SERVER)
    parser.add_argument("--domain", default=Config.LDAP_DOMAIN)
    parser.add_argument("--search-base", default=Config.LDAP_USER_SEARCH_BASE)
    parser.add_argument("--user", help="Username to test")
    parser.add_argument("--password", help="Password for user")
    args = parser.parse_args()

    print("==================================================")
    print("   RAGE N RAZE — WINDOWS ACTIVE DIRECTORY DIAGNOSTIC ")
    print("==================================================")
    print(f" Current Configuration:")
    print(f"   LDAP_SERVER:           {args.server}")
    print(f"   LDAP_DOMAIN:           {args.domain}")
    print(f"   LDAP_USER_SEARCH_BASE: {args.search_base}")
    print(f"   LDAP_ADMIN_GROUP:      {Config.LDAP_ADMIN_GROUP}")
    print(f"   LDAP_TECH_GROUP:       {Config.LDAP_TECH_GROUP}")

    username = args.user or input("\nEnter Windows Domain Username (e.g. Administrator): ").strip()
    if not username:
        return
    password = args.password or getpass.getpass(f"Enter password for {args.domain}\\{username}: ")

    # 1. First test native Windows Domain Logon (Works on Windows Server 2025 out of the box)
    if os.name == "nt":
        if test_windows_native_logon(args.domain, username, password, Config.LDAP_ADMIN_GROUP, Config.LDAP_TECH_GROUP):
            print("\n>> NATIVE WINDOWS AUTHENTICATION IS WORKING PERFECTLY! <<")
            return


if __name__ == "__main__":
    main()
