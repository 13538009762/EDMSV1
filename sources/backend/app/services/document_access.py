"""Document visibility and permission helpers."""
from __future__ import annotations

from typing import Optional

from app.models import Document, DocumentPermission, User


def user_effective_document_role(user: User, doc: Document) -> str:
    """用于 API / 列表展示：owner | edit | comment | view | approver | reader。"""
    if doc.owner_id == user.id:
        return "owner"
    if doc.status == "approved":
        return "reader"
    perm = DocumentPermission.query.filter_by(document_id=doc.id, user_id=user.id).first()
    if perm:
        return perm.role
    from app.models import ApprovalFlow, ApprovalParticipant

    flow = ApprovalFlow.query.filter_by(document_id=doc.id, status="active").first()
    if flow and ApprovalParticipant.query.filter_by(flow_id=flow.id, user_id=user.id).first():
        return "approver"
    if doc.status == "approved":
        return "reader"
    return "reader"


def user_can_view_document(user: User, doc: Document) -> bool:
    if doc.status == "approved":
        return True
    if doc.owner_id == user.id:
        return True
    perm = (
        DocumentPermission.query.filter_by(document_id=doc.id, user_id=user.id).first()
    )
    if perm:
        return True
    # participant in active flow
    from app.models import ApprovalFlow, ApprovalParticipant

    flow = ApprovalFlow.query.filter_by(document_id=doc.id, status="active").first()
    if flow:
        p = ApprovalParticipant.query.filter_by(flow_id=flow.id, user_id=user.id).first()
        if p:
            return True
    return False


def user_document_role(user: User, doc: Document) -> Optional[str]:
    if doc.owner_id == user.id:
        return "owner"
    perm = (
        DocumentPermission.query.filter_by(document_id=doc.id, user_id=user.id).first()
    )
    return perm.role if perm else None


def user_can_edit_metadata(user: User, doc: Document) -> bool:
    """标题、页面设置等元数据：与正文相同，仅草稿且为所有者或 edit 协作者。"""
    return user_can_edit_content(user, doc)


def user_can_edit_content(user: User, doc: Document) -> bool:
    if doc.status != "draft":
        return False
    if doc.owner_id == user.id:
        return True
    perm = (
        DocumentPermission.query.filter_by(
            document_id=doc.id, user_id=user.id, role="edit"
        ).first()
    )
    return perm is not None


def user_can_comment(user: User, doc: Document) -> bool:
    if doc.status not in ("draft", "in_approval"):
        return False
    if doc.owner_id == user.id:
        return True
    perm = DocumentPermission.query.filter_by(document_id=doc.id, user_id=user.id).first()
    if perm and perm.role in ("comment", "edit"):
        return True
    from app.models import ApprovalFlow, ApprovalParticipant

    flow = ApprovalFlow.query.filter_by(document_id=doc.id, status="active").first()
    if flow:
        if ApprovalParticipant.query.filter_by(flow_id=flow.id, user_id=user.id).first():
            return True
    return False
