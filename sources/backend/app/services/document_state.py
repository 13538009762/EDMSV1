"""文档生命周期状态机（与任务书一致）。

规则摘要：
- draft：可改正文；可批注（所有者 / edit|comment 协作者 / 审批参与者）。
- in_approval：不可改正文；可批注（同上）。
- approved：全员可读；不可编辑、不可新批注（仅可查看历史等）。
- rejected：不可编辑、不可批注；所有者可通过 new-version 回到 draft。
"""

from __future__ import annotations

from typing import Literal

from app.models import Document

DocumentStatus = Literal["draft", "in_approval", "approved", "rejected"]

VALID_STATUSES = frozenset({"draft", "in_approval", "approved", "rejected"})


def is_valid_status(s: str) -> bool:
    return s in VALID_STATUSES


def content_editable_status(doc: Document) -> bool:
    """正文是否允许保存/协作编辑（仅草稿）。"""
    return doc.status == "draft"


def comments_allowed_status(doc: Document) -> bool:
    """是否允许新增批注（草稿或审批中）。"""
    return doc.status in ("draft", "in_approval")
