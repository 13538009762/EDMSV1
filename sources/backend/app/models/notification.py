"""Notification model for global alerts."""
from datetime import datetime

from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(32), nullable=False, default="system")  # approval, mention, system
    title = db.Column(db.String(256), nullable=True, default="")
    content = db.Column(db.Text, nullable=True)  # JSON payload
    is_read = db.Column(db.Boolean, default=False)
    related_doc_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])
    related_doc = db.relationship("Document", foreign_keys=[related_doc_id])

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "is_read": self.is_read,
            "related_doc_id": self.related_doc_id,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
