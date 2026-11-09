"""
WSGI entry point for IIS and production servers (Waitress, HttpPlatformHandler, etc.).
"""

from app import app

if __name__ == "__main__":
    app.run()
