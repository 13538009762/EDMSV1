import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///edms.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = False  # demo; use timedelta hours=8 in prod
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ADMIN_IMPORT_TOKEN = os.environ.get("ADMIN_IMPORT_TOKEN", "admin123")

