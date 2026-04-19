"""Import master data from XLSX. Clears existing master tables first."""
from __future__ import annotations

import re
from datetime import date, datetime
from io import BytesIO
from typing import Any

from openpyxl import load_workbook

from app.extensions import db
from app.models import (
    ApprovalDecision,
    ApprovalFlow,
    ApprovalParticipant,
    AuditLog,
    Comment,
    Department,
    Document,
    DocumentVersion,
    DocumentPermission,
    Position,
    User,
)
import json
import uuid


def _create_tiptap_doc(content: list) -> dict:
    return {"type": "doc", "content": content}

def _create_heading(text: str, level: int = 1) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}]
    }

def _create_paragraph(text: str = "") -> dict:
    item = {"type": "paragraph"}
    if text:
        item["content"] = [{"type": "text", "text": text}]
    return item

def _create_bullet_list(items: list[str]) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": i}]}]
            } for i in items
        ]
    }

def init_standard_templates(admin_user_id: int | None = None):
    templates_data = [
        {
            "title": "Employment Contract",
            "content": _create_tiptap_doc([
                _create_heading("EMPLOYMENT AGREEMENT"),
                _create_paragraph("This Agreement is made on [DATE] between:"),
                _create_paragraph("PARTY A (EMPLOYER): [Organization Name]"),
                _create_paragraph("PARTY B (EMPLOYEE): [Full Name]"),
                _create_heading("1. Position and Responsibilities", 2),
                _create_paragraph("The Employee shall perform the following duties:"),
                _create_bullet_list(["Manage organizational workflow", "Report to department head", "Ensure quality compliance"]),
                _create_heading("2. Term and Compensation", 2),
                _create_paragraph("Salary: [Amount] per month. Effective Date: [Start Date].")
            ])
        },
        {
            "title": "Meeting Minutes",
            "content": _create_tiptap_doc([
                _create_heading("MEETING MINUTES"),
                _create_paragraph("DATE: [Enter Date] | TIME: [Enter Time]"),
                _create_paragraph("TOPIC: [Project/Department Meeting]"),
                _create_heading("Attendees", 2),
                _create_bullet_list(["[Name 1]", "[Name 2]", "[Name 3]"]),
                _create_heading("Agenda & Discussion", 2),
                _create_paragraph("[Details of discussions...]"),
                _create_heading("Action Items", 2),
                _create_bullet_list(["Task A - Assigned to [Name]", "Task B - Due [Date]"])
            ])
        },
        {
            "title": "Technical Specification",
            "content": _create_tiptap_doc([
                _create_heading("TECHNICAL SPECIFICATION"),
                _create_paragraph("VERSION: 1.0 | STATUS: Draft"),
                _create_heading("1. Overview", 2),
                _create_paragraph("Provide a high-level summary of the system or feature."),
                _create_heading("2. Requirements", 2),
                _create_bullet_list(["Requirement 1", "Requirement 2", "Requirement 3"]),
                _create_heading("3. Design & Architecture", 2),
                _create_paragraph("Describe components, data flow, and technologies used.")
            ])
        },
        {
            "title": "Weekly Report",
            "content": _create_tiptap_doc([
                _create_heading("WEEKLY PROGRESS REPORT"),
                _create_paragraph("PERIOD: [Start Date] to [End Date]"),
                _create_heading("Done This Week", 2),
                _create_bullet_list(["Completed Task A", "Delivered Feature B"]),
                _create_heading("Planned for Next Week", 2),
                _create_bullet_list(["Start Project C", "Review Milestone D"]),
                _create_heading("Risks & Blockers", 2),
                _create_paragraph("None.")
            ])
        },
        {
            "title": "Expense Report",
            "content": _create_tiptap_doc([
                _create_heading("EMPLOYEE EXPENSE REIMBURSEMENT"),
                _create_paragraph("SUBMITTED BY: [Employee name]"),
                _create_paragraph("DEPARTMENT: [Department]"),
                _create_heading("Expense Summary", 2),
                _create_paragraph("DATE | DESCRIPTION | CATEGORY | AMOUNT"),
                _create_paragraph("-------------------------------------------"),
                _create_paragraph("[Date] | [Travel/Lunch] | [Category] | [0.00]"),
                _create_paragraph("TOTAL: 0.00")
            ])
        }
    ]
    
    count = 0
    for tmpl in templates_data:
        doc = Document(
            owner_id=admin_user_id,
            title=tmpl["title"],
            status="approved",
            doc_number=f"TMPL-{uuid.uuid4().hex[:6].upper()}",
            is_template=True,
            is_public=True
        )
        db.session.add(doc)
        db.session.flush()
        
        ver = DocumentVersion(
            document_id=doc.id,
            version_no=1,
            content_json=json.dumps(tmpl["content"]),
            created_by_id=admin_user_id
        )
        db.session.add(ver)
        db.session.flush()
        doc.current_version_id = ver.id
        count += 1
    return count

def _norm_key(s: str) -> str:
    return re.sub(r"\s+", "", str(s).strip().lower()) if s is not None else ""


def _match_header(header_row: tuple[Any, ...]) -> dict[str, int]:
    """Map canonical field names to column indices."""
    mapping: dict[str, int] = {}
    aliases = [
        (
            "employee_no",
            [
                "员工编号",
                "empno",
                "employeeno",
                "编号",
                "employeeid",
                "emp.id",
                "empid",
            ],
        ),
        ("last_name", ["姓", "lastname", "surname"]),
        ("first_name", ["名", "firstname"]),
        ("patronymic", ["父称", "middlename", "中间名"]),
        ("birth_date", ["出生日期", "birthdate", "dateofbirth"]),
        ("gender", ["性别", "gender"]),
        ("login_name", ["登录名", "用户名", "login", "loginname"]),
        (
            "department_code",
            [
                "部门编号",
                "deptcode",
                "departmentcode",
                "departmentnumber",
                "department",
            ],
        ),
        (
            "department_name",
            ["部门名称", "部门", "name", "departmentname"],
        ),
        (
            "position_short",
            [
                "职务简称",
                "jobshort",
                "positionabbreviation",
                "position",
            ],
        ),
        (
            "position_full",
            ["职务全称", "fullname", "jobfull", "positionname"],
        ),
        (
            "manager_employee_no",
            ["直属上级员工编号", "上级", "manager", "managerid"],
        ),
    ]
    for idx, cell in enumerate(header_row):
        if cell is None:
            continue
        raw = str(cell).strip()
        nk = _norm_key(raw)
        for canonical, labels in aliases:
            for lb in labels:
                if _norm_key(lb) == nk:
                    mapping[canonical] = idx
                    break
            if canonical in mapping and mapping[canonical] == idx:
                break
    return mapping


def _parse_date(val: Any):
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%m/%d/%y", "%m/%d/%Y", "%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def import_master_data_xlsx(file_bytes: bytes) -> dict[str, Any]:
    """Replace all master data with content from workbook."""
    wb = load_workbook(filename=BytesIO(file_bytes), read_only=True, data_only=True)

    dept_rows: list[tuple[str, str]] = []
    pos_rows: list[tuple[str, str]] = []
    emp_rows: list[dict[str, Any]] = []
    mgr_rows: list[dict[str, Any]] = []

    for sheet_name in wb.sheetnames:
        sn = _norm_key(sheet_name)
        sheet = wb[sheet_name]
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue
        header = rows[0]

        if "部门" in sheet_name or sn == "departments" or sn == "dept":
            keys = _match_header(header)
            if "department_code" in keys and "department_name" in keys:
                for r in rows[1:]:
                    if not r or r[keys["department_code"]] is None:
                        continue
                    code = str(r[keys["department_code"]]).strip()
                    name = str(r[keys["department_name"]] or code).strip()
                    if code:
                        dept_rows.append((code, name))
            elif len(header) >= 2:
                for r in rows[1:]:
                    if r and r[0] is not None:
                        dept_rows.append((str(r[0]).strip(), str(r[1] or r[0]).strip()))

        elif "职务" in sheet_name or "position" in sn:
            keys = _match_header(header)
            if "position_short" in keys and "position_full" in keys:
                for r in rows[1:]:
                    if not r:
                        continue
                    ps = r[keys["position_short"]]
                    if ps is None:
                        continue
                    pf = r[keys["position_full"]] or ps
                    pos_rows.append((str(ps).strip(), str(pf).strip()))
            elif len(header) >= 2:
                for r in rows[1:]:
                    if r and r[0] is not None:
                        pos_rows.append((str(r[0]).strip(), str(r[1] or r[0]).strip()))

        elif "管理" in sheet_name or "manager" in sn:
            keys = _match_header(header)
            if "login_name" in keys:
                for r in rows[1:]:
                    if not r or r[keys["login_name"]] is None:
                        continue
                    rowd: dict[str, Any] = {}
                    for k, ci in keys.items():
                        rowd[k] = r[ci] if ci < len(r) else None
                    rowd["_is_manager"] = True
                    mgr_rows.append(rowd)

        elif "员工" in sheet_name or "employ" in sn or sn == "staff":
            keys = _match_header(header)
            if "login_name" in keys:
                for r in rows[1:]:
                    if not r or r[keys["login_name"]] is None:
                        continue
                    rowd = {k: (r[ci] if ci < len(r) else None) for k, ci in keys.items()}
                    rowd["_is_manager"] = False
                    emp_rows.append(rowd)

    # Fallback: first sheets heuristic
    if not dept_rows and wb.sheetnames:
        sh = wb[wb.sheetnames[0]]
        rows = list(sh.iter_rows(values_only=True))
        if rows and len(rows[0]) >= 2:
            for r in rows[1:]:
                if r and r[0]:
                    dept_rows.append((str(r[0]).strip(), str(r[1] or r[0]).strip()))

    errors: list[str] = []

    def flush_all():
        """Clear business + master data so user FKs can be recreated."""
        from sqlalchemy import delete, select

        db.session.execute(delete(ApprovalDecision))
        db.session.execute(delete(ApprovalParticipant))
        db.session.execute(delete(ApprovalFlow))
        db.session.execute(delete(AuditLog))
        db.session.execute(delete(Comment))
        db.session.execute(delete(DocumentPermission))
        for doc in db.session.scalars(select(Document)).all():
            db.session.delete(doc)
        db.session.execute(delete(User))
        db.session.execute(delete(Position))
        db.session.execute(delete(Department))
        db.session.flush()

    flush_all()

    code_to_dept: dict[str, Department] = {}
    for code, name in dept_rows:
        if not code:
            continue
        d = Department(code=code, name=name)
        db.session.add(d)
        db.session.flush()
        code_to_dept[code] = d

    seen_pos: dict[str, Position] = {}
    for ps, pf in pos_rows:
        if ps in seen_pos:
            continue
        p = Position(short_name=ps, full_name=pf)
        db.session.add(p)
        db.session.flush()
        seen_pos[ps] = p

    def upsert_user(row: dict[str, Any]) -> None:
        login = str(row.get("login_name") or "").strip()
        if not login:
            return
        emp_no = str(row.get("employee_no") or login).strip()
        dept_code = row.get("department_code")
        dept_id = None
        if dept_code is not None:
            dc = str(dept_code).strip()
            if dc in code_to_dept:
                dept_id = code_to_dept[dc].id
        u = User(
            employee_no=emp_no,
            last_name=str(row.get("last_name") or "-").strip(),
            first_name=str(row.get("first_name") or "-").strip(),
            patronymic=str(row.get("patronymic") or "").strip(),
            birth_date=_parse_date(row.get("birth_date")),
            gender=str(row.get("gender") or "").strip(),
            login_name=login,
            department_id=dept_id,
            position_short=str(row.get("position_short") or "").strip(),
            manager_employee_no=str(row.get("manager_employee_no") or "").strip(),
            is_manager=bool(row.get("_is_manager")),
        )
        db.session.add(u)

    merged: dict[str, dict[str, Any]] = {}
    for row in emp_rows + mgr_rows:
        login = str(row.get("login_name") or "").strip()
        if not login:
            continue
        if login not in merged:
            merged[login] = row
        else:
            merged[login]["_is_manager"] = merged[login].get("_is_manager") or row.get(
                "_is_manager"
            )

    for row in merged.values():
        try:
            upsert_user(row)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{row.get('login_name')}: {exc}")

    db.session.flush()
    
    # Initialize standard templates after users are created
    admin_user = db.session.query(User).filter_by(login_name='admin').first() or db.session.query(User).first()
    admin_id = admin_user.id if admin_user else None
    tmpl_count = init_standard_templates(admin_id)

    # The calling API handler should commit the transaction.
    return {
        "departments": len(dept_rows),
        "positions": len(pos_rows),
        "users": len(merged),
        "templates": tmpl_count,
        "errors": errors,
    }
