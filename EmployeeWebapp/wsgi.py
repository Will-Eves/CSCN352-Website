"""
WSGI entry point for IIS and production servers (Waitress, HttpPlatformHandler, etc.).
"""

import sys
import os

# Ensure the application directory is always at the front of sys.path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app import app

if __name__ == "__main__":
    app.run()
