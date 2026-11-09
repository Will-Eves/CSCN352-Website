"""
Rage N Raze — LDAP & Active Directory Diagnostic Tool
=====================================================
Run this script directly in PowerShell/CMD on your server to troubleshoot
LDAP connectivity, domain bindings, user searches, and group role mapping.

Usage:
    python test_ldap.py
    python test_ldap.py --user Administrator --password YourPassword
"""

import sys
import os
import socket
import argparse
import getpass

# Add current dir to path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

try:
    from ldap3 import Server, Connection, ALL, SUBTREE
    from ldap3.core.exceptions import LDAPException, LDAPSocketOpenError, LDAPBindError
except ImportError:
    print("[ERROR] ldap3 is not installed. Run: pip install ldap3")
    sys.exit(1)


def parse_host_port(server_uri: str):
    """Extract hostname and port from an ldap URI."""
    uri = server_uri.replace("ldap://", "").replace("ldaps://", "")
    if ":" in uri:
        host, port = uri.split(":", 1)
        return host, int(port)
    port = 636 if server_uri.startswith("ldaps://") else 389
    return uri, port


def test_tcp_connectivity(host: str, port: int) -> bool:
    print(f"\n[1/4] Testing TCP network connectivity to {host}:{port} ...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        sock.close()
        print(f"  [OK] Successfully established TCP connection to {host}:{port}")
        return True
    except socket.gaierror as e:
        print(f"  [FAIL] DNS resolution failed for '{host}': {e}")
        print("  --> HINT: Check if the hostname is spelled correctly in config.py or use an IP address.")
        return False
    except socket.timeout:
        print(f"  [FAIL] Connection to {host}:{port} timed out after 5 seconds.")
        print("  --> HINT: Check Windows Firewall on the DC (port 389 must be open).")
        return False
    except Exception as e:
        print(f"  [FAIL] Could not connect to {host}:{port}: {e}")
        return False


def test_ldap_bind(server_uri: str, domain: str, username: str, password: str):
    print(f"\n[2/4] Testing LDAP bind for user '{domain}\\{username}' ...")
    bind_dn = f"{domain}\\{username}"
    
    try:
        server = Server(server_uri, get_info=ALL)
        conn = Connection(server, user=bind_dn, password=password, auto_bind=True)
        print(f"  [OK] LDAP Bind Successful! Authenticated as: {bind_dn}")
        return conn, server
    except LDAPBindError as e:
        print(f"  [FAIL] LDAP Bind Error: {e}")
        err_str = str(e)
        if "data 52e" in err_str:
            print("  --> HINT (52e): Invalid credentials (wrong password or username).")
        elif "data 525" in err_str:
            print("  --> HINT (525): User not found in domain.")
        elif "data 532" in err_str:
            print("  --> HINT (532): Password has expired.")
        elif "data 533" in err_str:
            print("  --> HINT (533): User account is disabled.")
        elif "data 701" in err_str:
            print("  --> HINT (701): Account expired.")
        elif "data 775" in err_str:
            print("  --> HINT (775): User account is locked out.")
        else:
            print(f"  --> Check if domain '{domain}' matches your NetBIOS domain name.")
        return None, None
    except LDAPSocketOpenError as e:
        print(f"  [FAIL] Socket open error: {e}")
        return None, None
    except Exception as e:
        print(f"  [FAIL] Unexpected error during bind: {e}")
        return None, None


def test_user_search(conn, search_base: str, username: str, admin_grp: str, tech_grp: str):
    print(f"\n[3/4] Searching for user attributes in '{search_base}' ...")
    search_filter = f"(sAMAccountName={username})"

    try:
        conn.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=["displayName", "mail", "sAMAccountName", "memberOf", "distinguishedName"],
        )

        if not conn.entries:
            print(f"  [WARN] User '{username}' was authenticated, but no entry was found under search base:")
            print(f"         '{search_base}'")
            print("  --> HINT: If your users are in the default Active Directory container,")
            print("      the search base is usually 'CN=Users,DC=...' (not 'OU=Users,...'),")
            print("      or you can set LDAP_USER_SEARCH_BASE to the domain root (e.g. 'DC=rnr,DC=local').")
            return

        entry = conn.entries[0]
        print(f"  [OK] User Found: {entry.distinguishedName}")
        print(f"       Display Name: {getattr(entry, 'displayName', 'None')}")
        print(f"       Email:        {getattr(entry, 'mail', 'None')}")

        # Test group membership
        print(f"\n[4/4] Checking group memberships for role mapping ...")
        member_of_raw = entry.memberOf.values if hasattr(entry, "memberOf") and entry.memberOf else []
        member_of = [str(g) for g in member_of_raw]

        print(f"       Groups user belongs to ({len(member_of)}):")
        for g in member_of:
            print(f"         - {g}")

        role = "viewer"
        for group_dn in member_of:
            group_dn_upper = group_dn.upper()
            if f"CN={admin_grp}".upper() in group_dn_upper:
                role = "admin"
                break
            if f"CN={tech_grp}".upper() in group_dn_upper:
                role = "technician"

        print(f"\n  ==================================================")
        print(f"  RESULT: User '{username}' maps to role: [{role.upper()}]")
        print(f"  ==================================================")
        if role == "viewer":
            print(f"  Note: To give this user admin rights, add them to group '{admin_grp}' in Active Directory,")
            print(f"        or promote them via the webapp's Admin Panel.")

    except LDAPException as e:
        print(f"  [FAIL] Search error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Test and diagnose Active Directory LDAP connectivity.")
    parser.add_argument("--server", default=Config.LDAP_SERVER, help=f"LDAP Server URI (default: {Config.LDAP_SERVER})")
    parser.add_argument("--domain", default=Config.LDAP_DOMAIN, help=f"NetBIOS Domain (default: {Config.LDAP_DOMAIN})")
    parser.add_argument("--search-base", default=Config.LDAP_USER_SEARCH_BASE, help=f"User search base (default: {Config.LDAP_USER_SEARCH_BASE})")
    parser.add_argument("--user", help="Username to test (without domain)")
    parser.add_argument("--password", help="Password for user")
    args = parser.parse_args()

    print("==================================================")
    print("   RAGE N RAZE — LDAP ACTIVE DIRECTORY DIAGNOSTIC ")
    print("==================================================")
    print(f" Current Configuration (from config.py / env):")
    print(f"   LDAP_SERVER:           {args.server}")
    print(f"   LDAP_DOMAIN:           {args.domain}")
    print(f"   LDAP_USER_SEARCH_BASE: {args.search_base}")
    print(f"   LDAP_ADMIN_GROUP:      {Config.LDAP_ADMIN_GROUP}")
    print(f"   LDAP_TECH_GROUP:       {Config.LDAP_TECH_GROUP}")
    print(f"   LDAP_VIEWER_GROUP:     {Config.LDAP_VIEWER_GROUP}")

    username = args.user
    if not username:
        username = input("\nEnter Windows Domain Username (e.g. Administrator): ").strip()
    if not username:
        print("Username is required.")
        return

    password = args.password
    if not password:
        password = getpass.getpass(f"Enter password for {args.domain}\\{username}: ")

    host, port = parse_host_port(args.server)

    # Step 1: TCP Port
    if not test_tcp_connectivity(host, port):
        return

    # Step 2: Bind
    conn, server = test_ldap_bind(args.server, args.domain, username, password)
    if not conn:
        return

    # Step 3 & 4: Search & Role Mapping
    test_user_search(conn, args.search_base, username, Config.LDAP_ADMIN_GROUP, Config.LDAP_TECH_GROUP)

    try:
        conn.unbind()
    except Exception:
        pass


if __name__ == "__main__":
    main()
