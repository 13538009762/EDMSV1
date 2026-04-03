from datetime import datetime

from app.extensions import db


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    document_version_id = db.Column(db.Integer, db.ForeignKey("document_versions.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    anchor_json = db.Column(db.Text, nullable=True)  # {"from":int,"to":int} text selection
    status = db.Column(db.String(32), nullable=False, default="active")  # active, resolved
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True)
    hidden_when_resolved = db.Column(db.Boolean, default=False)  # UI: hide completed thread in editor
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    document_version = db.relationship(
        "DocumentVersion",
        back_populates="comments",
    )
    author = db.relationship("User", foreign_keys=[author_id])
    parent = db.relationship("Comment", remote_side=[id])
