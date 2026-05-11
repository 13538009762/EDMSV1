from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.extensions import db




document_spaces = db.Table(
    "document_spaces",
    db.Column("document_id", db.Integer, db.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    db.Column("space_id", db.Integer, db.ForeignKey("spaces.id", ondelete="CASCADE"), primary_key=True),
)



class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    doc_number = db.Column(db.String(64), unique=True, nullable=True) # YYYYMMDDXXX
    title = db.Column(db.String(512), nullable=False, default="Untitled")
    status = db.Column(
        db.String(32), nullable=False, default="draft"
    )  # draft, in_approval, approved, rejected
    is_public = db.Column(db.Boolean, default=False)
    current_version_id = db.Column(db.Integer, db.ForeignKey("document_versions.id"), nullable=True)
    page_settings_json = db.Column(db.Text, nullable=True)  # JSON string
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=True)
    is_template = db.Column(db.Boolean, default=False)
    template_description = db.Column(db.String(512), nullable=True)  # Description shown in Template Gallery
    template_icon = db.Column(db.String(64), nullable=True) # Icon name (e.g., from Element Plus icons)
    doc_type = db.Column(db.String(32), default="rich_text") # rich_text, pdf
    deleted_at = db.Column(db.DateTime, nullable=True)  # soft delete for recycle bin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === 区块链存证字段 ===
    file_hash = db.Column(db.String(256), nullable=True)
    tx_hash = db.Column(db.String(256), nullable=True)

    owner = db.relationship("User", back_populates="documents_owned", foreign_keys=[owner_id])
    current_version = db.relationship(
        "DocumentVersion",
        foreign_keys=[current_version_id],
        post_update=True,
    )
    versions = db.relationship(
        "DocumentVersion",
        back_populates="document",
        foreign_keys="DocumentVersion.document_id",
        order_by="DocumentVersion.version_no",
        cascade="all, delete-orphan",
    )
    permissions = db.relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")
    approval_flows = db.relationship("ApprovalFlow", back_populates="document", cascade="all, delete-orphan")
    spaces = db.relationship("Space", secondary="document_spaces", back_populates="documents")
    parent = db.relationship("Document", remote_side="Document.id", foreign_keys=[parent_id], backref=db.backref("children", lazy="dynamic"))

    @property
    def space(self):
        """Backward compatibility for single space access."""
        return self.spaces[0] if self.spaces else None


class DocumentVersion(db.Model):
    __tablename__ = "document_versions"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    version_no = db.Column(db.Integer, nullable=False, default=1)
    content_json = db.Column(db.Text, nullable=True)  # TipTap / ProseMirror JSON
    yjs_state = db.Column(db.LargeBinary, nullable=True)
    file_path = db.Column(db.String(512), nullable=True) # Path for PDF/Binary files
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    parent_version_id = db.Column(db.Integer, db.ForeignKey("document_versions.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    document = db.relationship(
        "Document",
        back_populates="versions",
        foreign_keys=[document_id],
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    comments = db.relationship(
        "Comment",
        back_populates="document_version",
        cascade="all, delete-orphan",
    )

    @staticmethod
    def default_content_json() -> str:
        import json

        return json.dumps(
            {
                "type": "doc",
                "content": [{"type": "paragraph", "content": []}],
            }
        )


class DocumentPermission(db.Model):
    __tablename__ = "document_permissions"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(32), nullable=False)  # view, edit, comment

    document = db.relationship("Document", back_populates="permissions")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("document_id", "user_id", name="uq_doc_user_perm"),
    )
