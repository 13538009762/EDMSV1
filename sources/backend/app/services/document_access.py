"""Document visibility and permission helpers."""
from __future__ import annotations

from typing import Optional

from app.models import Document, DocumentPermission, User


def user_effective_document_role(user: User, doc: Document) -> str:
    """用于 API / 列表展示：owner | edit | comment | view | approver | reader。"""
    if doc.owner_id == user.id:
        return "owner"
    
    perm = DocumentPermission.query.filter_by(document_id=doc.id, user_id=user.id).first()
    
    from app.models import ApprovalFlow, ApprovalParticipant
    # Check current or past approvers
    flows = ApprovalFlow.query.filter_by(document_id=doc.id).all()
    for f in flows:
        if ApprovalParticipant.query.filter_by(flow_id=f.id, user_id=user.id).first():
            return "approver"

    # If approved, contributors can only view or comment
    if doc.status == "approved":
        if perm:
            if perm.role == "edit":
                return "view"
            return perm.role
        if doc.is_public:
            return "reader"
        return "view"

    if perm:
        return perm.role

    return "reader"


def user_can_view_document(user: User, doc: Document) -> bool:
    if user.login_name == 'admin' or doc.owner_id == user.id:
        return True
    if doc.status == "approved" and doc.is_public:
        return True
    perm = (
        DocumentPermission.query.filter_by(document_id=doc.id, user_id=user.id).first()
    )
    if perm:
        return True
    
    from app.models import ApprovalFlow, ApprovalParticipant
    flows = ApprovalFlow.query.filter_by(document_id=doc.id).all()
    for flow in flows:
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
    """标题、页面设置、归类等元数据：允许所有者或管理员在任何阶段修改（用于归档/分类）。"""
    if user.login_name == 'admin' or doc.owner_id == user.id:
        return True
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
    if doc.status not in ("draft", "in_approval", "approved"):
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


def user_can_manage_permissions(user: User, doc: Document) -> bool:
    """Check if user can change sharing settings or public visibility."""
    # 1. Admin always has full control
    if user.login_name == 'admin':
        return True
        
    # 2. Owner always has control
    if doc.owner_id == user.id:
        return True
        
    # 3. Special rules for Approved documents
    if doc.status == "approved":
        # 部门经理可以管理本部门已审批通过的文档
        if user.is_manager and user.department_id == doc.owner.department_id:
            return True
            
        # 审批过该文档的人也可以管理权限
        from app.models import ApprovalFlow, ApprovalParticipant
        flows = ApprovalFlow.query.filter_by(document_id=doc.id).all()
        for flow in flows:
            p = ApprovalParticipant.query.filter_by(flow_id=flow.id, user_id=user.id).first()
            if p:
                return True
                
    return False
