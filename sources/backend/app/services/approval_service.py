"""Approval workflow transitions."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.extensions import db
from app.models import Document
from app.models.workflow import (
    ApprovalDecision,
    ApprovalFlow,
    ApprovalParticipant,
)


def cancel_active_flows(document_id: int) -> None:
    flows = ApprovalFlow.query.filter_by(document_id=document_id, status="active").all()
    for f in flows:
        f.status = "cancelled"


def start_flow(
    document: Document,
    flow_type: str,
    approver_user_ids: list[int],
) -> ApprovalFlow:
    """Create active approval flow; document must be draft."""
    if document.status != "draft":
        raise ValueError("Document must be draft")
    if not approver_user_ids:
        raise ValueError("At least one approver")
    cancel_active_flows(document.id)
    flow = ApprovalFlow(
        document_id=document.id,
        flow_type=flow_type,
        status="active",
        current_order=1,
    )
    db.session.add(flow)
    db.session.flush()
    for i, uid in enumerate(approver_user_ids, start=1):
        db.session.add(
            ApprovalParticipant(flow_id=flow.id, user_id=uid, step_order=i),
        )
    document.status = "in_approval"
    document.updated_at = datetime.utcnow()
    db.session.flush()
    return flow


def apply_decision(
    participant: ApprovalParticipant,
    decision: str,
    reason: Optional[str],
    document: Document,
) -> None:
    if participant.flow.status != "active":
        raise ValueError("Flow not active")
    if participant.decision:
        raise ValueError("Already decided")
    flow = participant.flow
    if flow.flow_type == "sequential":
        if participant.step_order != flow.current_order:
            raise ValueError("Not your turn in sequential flow")

    new_decision = ApprovalDecision(
        participant_id=participant.id,
        decision=decision,
        reason=reason or "",
    )
    participant.decision = new_decision
    
    db.session.add(new_decision)
    db.session.flush()

    if decision == "reject":
        flow.status = "rejected"
        document.status = "rejected"
        document.updated_at = datetime.utcnow()
        return

    if flow.flow_type == "parallel":
        # 现在 participant.decision 在内存里有值了，pending 计算就会完全准确
        pending = [p for p in flow.participants if not p.decision]
        if not pending:
            if all(
                p.decision and p.decision.decision == "approve" for p in flow.participants
            ):
                flow.status = "completed"
                document.status = "approved"
            else:
                flow.status = "rejected"
                document.status = "rejected"
        document.updated_at = datetime.utcnow()
        return

    # sequential approve
    orders = sorted({p.step_order for p in flow.participants})
    idx = orders.index(flow.current_order)
    if idx + 1 < len(orders):
        flow.current_order = orders[idx + 1]
    else:
        flow.status = "completed"
        document.status = "approved"
    document.updated_at = datetime.utcnow()