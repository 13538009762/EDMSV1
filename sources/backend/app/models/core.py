from datetime import date
from typing import TYPE_CHECKING

from app.extensions import db

if TYPE_CHECKING:
    from app.models.document import Document


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(256), nullable=False)

    users = db.relationship("User", back_populates="department")


class Position(db.Model):
    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True)
    short_name = db.Column(db.String(128), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(256), nullable=False)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    employee_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    last_name = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(128), nullable=False)
    patronymic = db.Column(db.String(128), default="")
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(32), default="")
    login_name = db.Column(db.String(128), unique=True, nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    position_short = db.Column(db.String(128), default="")
    manager_employee_no = db.Column(db.String(64), default="")
    is_manager = db.Column(db.Boolean, default=False)

    department = db.relationship("Department", back_populates="users")
    documents_owned = db.relationship(
        "Document", back_populates="owner", foreign_keys="Document.owner_id"
    )

    def display_name(self) -> str:
        parts = [self.last_name, self.first_name]
        return " ".join(p for p in parts if p)
