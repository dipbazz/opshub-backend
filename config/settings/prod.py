"""Production settings — used by the Docker image deployed to the droplet."""

from decouple import Csv, config

from .base import *  # noqa: F403

DEBUG = False

# CORS_ALLOWED_ORIGINS: set via env once the domain is known (Day 6).
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())

# Trust the Nginx reverse proxy's forwarded scheme when deciding if a
# request was HTTPS (Gunicorn itself only ever sees plain HTTP from Nginx).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days, raise once HTTPS is confirmed stable
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
