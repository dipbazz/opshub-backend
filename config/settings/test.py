"""
Settings for the PyTest run (local and CI).

SQLite in-memory keeps the suite fast and dependency-free (no Postgres
service needed just to run tests); nothing in the model layer relies on a
Postgres-specific feature. LocMemCache (not a dummy/no-op cache) is
"""

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = "test-secret-key-not-for-production"  # noqa: S105

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Hashing real passwords in every test is pure wasted CPU.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
