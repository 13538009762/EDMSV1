from datetime import datetime

from app.extensions import db


class ApprovalFlow(db.Model):
    __tablename__ = "approval_flows"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    flow_type = db.Column(db.String(32), nullable=False)  # parallel, sequential
    status = db.Column(db.String(32), nullable=False, default="active")  # active, completed, rejected
    current_order = db.Column(db.Integer, default=1)  # for sequential: min step pending
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    document = db.relationship("Document", backref="approval_flows")
    participants = db.relationship(
        "ApprovalParticipant",
        back_populates="flow",
        order_by="ApprovalParticipant.step_order",
        cascade="all, delete-orphan",
    )


class ApprovalParticipant(db.Model):
    __tablename__ = "approval_participants"

    id = db.Column(db.Integer, primary_key=True)
    flow_id = db.Column(db.Integer, db.ForeignKey("approval_flows.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    step_order = db.Column(db.Integer, nullable=False, default=1)

    flow = db.relationship("ApprovalFlow", back_populates="participants")
    user = db.relationship("User")
    decision = db.relationship(
        "ApprovalDecision",
        back_populates="participant",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ApprovalDecision(db.Model):
    __tablename__ = "approval_decisions"

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("approval_participants.id"), unique=True, nullable=False)
    decision = db.Column(db.String(32), nullable=False)  # approve, reject
    reason = db.Column(db.Text, nullable=True)
    decided_at = db.Column(db.DateTime, default=datetime.utcnow)

    participant = db.relationship("ApprovalParticipant", back_populates="decision")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    document_version_id = db.Column(db.Integer, db.ForeignKey("document_versions.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    summary = db.Column(db.String(512), nullable=False)
    payload_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
