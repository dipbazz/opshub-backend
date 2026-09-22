"""Local development settings — used inside docker-compose (web service)."""

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Vite's actual default dev server port (verified: no port override in
# opshub-frontend/vite.config.ts or package.json scripts). 3000 is CRA's
# default, not Vite's — don't reintroduce that mix-up.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
