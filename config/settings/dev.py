"""Local development settings — used inside docker-compose (web service)."""

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# The Vite dev server's default port.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
