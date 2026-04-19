"""Enterprise Workspace (Space) model."""
from datetime import datetime

from app.extensions import db


class Space(db.Model):
    __tablename__ = "spaces"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True, default="")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("User", foreign_keys=[owner_id])
    documents = db.relationship("Document", back_populates="space", lazy="dynamic")

    def __repr__(self):
        return f"<Space {self.id} '{self.name}'>"
