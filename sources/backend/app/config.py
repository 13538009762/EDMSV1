import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///edms.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 20,        # Allow up to 20 persistent connections
        "max_overflow": 40,     # Allow 40 additional overflow connections
        "pool_recycle": 300,    # Recycle connections after 5 minutes
        "pool_pre_ping": True,  # Test connection health before use
        "pool_timeout": 10,     # Only wait 10s for a connection (fail fast)
    }
    JWT_ACCESS_TOKEN_EXPIRES = False  # demo; use timedelta hours=8 in prod
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ADMIN_IMPORT_TOKEN = os.environ.get("ADMIN_IMPORT_TOKEN", "admin123")

