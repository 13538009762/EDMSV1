import pytest
import os

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL_TEST", "mysql+pymysql://root:123456@127.0.0.1:3306/edms_db_test"),
        JWT_SECRET_KEY="test-jwt",
        SECRET_KEY="test-secret",
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
