"""
EDMS V2.0 — Database Seeding Script
Populates the DB with demo data: departments, users, spaces, templates, and sample documents.

Usage:
    cd sources/backend
    python -m bin.seed_data
"""
import json
import sys
import os

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from app.extensions import db
from app.models import (
    Department, Position, User, Document, DocumentVersion, Space,
)


def _tiptap_doc(*paragraphs):
    """Build a minimal TipTap JSON doc from plain-text paragraphs."""
    content = []
    for text in paragraphs:
        content.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": text}] if text else [],
        })
    return json.dumps({"type": "doc", "content": content})


# ── Template content ────────────────────────────────────────────────
TEMPLATES = [
    {
        "title": "Employment Contract",
        "desc": "Standard employment agreement template",
        "content": _tiptap_doc(
            "EMPLOYMENT CONTRACT",
            "",
            "This Employment Contract is entered into between [Company Name] (the \"Employer\") and [Employee Name] (the \"Employee\").",
            "",
            "1. Position and Duties",
            "The Employee shall serve as [Job Title] and perform duties as assigned by the Employer.",
            "",
            "2. Compensation",
            "The Employee shall receive a monthly salary of [Amount] RMB, payable on the last business day of each month.",
            "",
            "3. Term of Employment",
            "This contract is effective from [Start Date] and shall remain in effect until [End Date] unless terminated earlier.",
            "",
            "4. Confidentiality",
            "The Employee agrees to maintain strict confidentiality of all proprietary information.",
            "",
            "Signatures:",
            "Employer: ________________    Date: ________",
            "Employee: ________________    Date: ________",
        ),
    },
    {
        "title": "Meeting Minutes",
        "desc": "Standard meeting minutes template",
        "content": _tiptap_doc(
            "MEETING MINUTES",
            "",
            "Date: [YYYY-MM-DD]",
            "Time: [HH:MM] - [HH:MM]",
            "Location: [Room / Online]",
            "Attendees: [Names]",
            "",
            "1. Agenda Items",
            "   1.1 [Topic 1] — Presented by [Name]",
            "   1.2 [Topic 2] — Presented by [Name]",
            "",
            "2. Discussion Summary",
            "   [Key points discussed]",
            "",
            "3. Action Items",
            "   - [Task] — Assigned to [Name] — Due [Date]",
            "",
            "4. Next Meeting",
            "   Date: [YYYY-MM-DD]  Time: [HH:MM]",
        ),
    },
    {
        "title": "Technical Specification",
        "desc": "Engineering technical specification template",
        "content": _tiptap_doc(
            "TECHNICAL SPECIFICATION",
            "",
            "Project: [Project Name]",
            "Version: 1.0",
            "Author: [Name]",
            "Date: [YYYY-MM-DD]",
            "",
            "1. Overview",
            "   [Brief description of the system or feature]",
            "",
            "2. Requirements",
            "   2.1 Functional Requirements",
            "   2.2 Non-Functional Requirements",
            "",
            "3. System Architecture",
            "   [Architecture description and diagrams]",
            "",
            "4. API Design",
            "   Endpoint: [METHOD] /api/[resource]",
            "   Request: { }",
            "   Response: { }",
            "",
            "5. Database Schema",
            "   [Table definitions]",
            "",
            "6. Testing Strategy",
            "   [Unit tests, integration tests, etc.]",
        ),
    },
    {
        "title": "Weekly Report",
        "desc": "Employee weekly status report",
        "content": _tiptap_doc(
            "WEEKLY REPORT",
            "",
            "Employee: [Name]",
            "Department: [Department]",
            "Week: [YYYY-MM-DD] to [YYYY-MM-DD]",
            "",
            "1. Completed This Week",
            "   - [Task 1]",
            "   - [Task 2]",
            "",
            "2. In Progress",
            "   - [Task 3] — [% complete]",
            "",
            "3. Planned for Next Week",
            "   - [Task 4]",
            "",
            "4. Blockers / Risks",
            "   - [Issue description]",
        ),
    },
    {
        "title": "Expense Report",
        "desc": "Business expense reimbursement form",
        "content": _tiptap_doc(
            "EXPENSE REPORT",
            "",
            "Employee: [Name]           Employee ID: [ID]",
            "Department: [Department]    Date: [YYYY-MM-DD]",
            "",
            "Purpose of Expense: [Business reason]",
            "",
            "Item Details:",
            "1. [Date] | [Description] | [Amount] RMB",
            "2. [Date] | [Description] | [Amount] RMB",
            "3. [Date] | [Description] | [Amount] RMB",
            "",
            "Total Amount: [Sum] RMB",
            "",
            "Approvals:",
            "Manager: ________________    Date: ________",
            "Finance: ________________    Date: ________",
        ),
    },
]

# ── Departments ─────────────────────────────────────────────────────
DEPARTMENTS = [
    ("RND", "Research & Development"),
    ("HR", "Human Resources"),
    ("FIN", "Finance"),
    ("EXEC", "Executive Office"),
]

# ── Users (login_name, first_name, last_name, dept_code, is_manager) ──
USERS = [
    ("admin", "Admin", "System", "EXEC", True),
    ("zhangwei", "Wei", "Zhang", "RND", True),
    ("lina", "Na", "Li", "HR", True),
    ("wangfang", "Fang", "Wang", "FIN", True),
    ("liuyang", "Yang", "Liu", "RND", False),
    ("chenxiao", "Xiao", "Chen", "RND", False),
    ("zhaoming", "Ming", "Zhao", "HR", False),
    ("sunli", "Li", "Sun", "FIN", False),
    ("wugang", "Gang", "Wu", "RND", False),
    ("zhoujie", "Jie", "Zhou", "EXEC", False),
]

# ── Spaces ──────────────────────────────────────────────────────────
SPACES = [
    ("Company Policies", "Official company policies and guidelines"),
    ("Tech Specifications", "Engineering design documents and API specs"),
    ("HR Documents", "HR forms, contracts, and employee handbooks"),
]

# ── Sample document titles for bulk generation ──────────────────────
SAMPLE_TITLES = [
    "Q1 2026 Revenue Report", "Employee Onboarding Guide", "API Gateway Design",
    "Annual Leave Policy Update", "Cloud Migration Plan", "Security Audit Findings",
    "Product Roadmap 2026", "Team Building Event Plan", "Budget Proposal FY2026",
    "Code Review Guidelines", "Customer Feedback Summary", "Server Monitoring Setup",
    "Marketing Campaign Brief", "Vendor Contract Review", "Sprint 12 Retrospective",
    "Data Backup Strategy", "Office Renovation Plan", "Patent Application Draft",
    "Quarterly OKR Review", "Disaster Recovery Plan", "New Hire Training Schedule",
    "Mobile App Requirements", "Sales Commission Structure", "DevOps Pipeline Design",
    "Compliance Checklist", "Brand Guidelines v3", "Performance Review Template",
    "Network Architecture Doc", "Travel Expense Policy", "R&D Lab Equipment List",
    "Investor Presentation", "Supply Chain Analysis", "Customer Support SOP",
    "Database Optimization Report", "Year-End Bonus Criteria", "Innovation Program",
    "IT Asset Inventory", "Office Safety Manual", "Partner Integration Guide",
    "A/B Testing Results", "Recruitment Pipeline Q2", "Technical Debt Tracker",
    "Cross-Team Sync Notes", "License Renewal Status", "Quality Assurance Plan",
    "Feature Flag Strategy", "Intern Program Guide", "System Upgrade Schedule",
    "UI/UX Style Guide", "Knowledge Base Outline",
]


def run_seed():
    """Main seeding function — idempotent."""
    print("🌱 Starting EDMS V2.0 database seeding...")

    # 1 ── Departments
    dept_map = {}
    for code, name in DEPARTMENTS:
        existing = Department.query.filter_by(code=code).first()
        if existing:
            dept_map[code] = existing
            continue
        d = Department(code=code, name=name)
        db.session.add(d)
        db.session.flush()
        dept_map[code] = d
    print(f"   ✅ {len(dept_map)} departments ready")

    # 2 ── Positions
    for sn, fn in [("staff", "Staff Member"), ("manager", "Department Manager"), ("director", "Director")]:
        if not Position.query.filter_by(short_name=sn).first():
            db.session.add(Position(short_name=sn, full_name=fn))
    db.session.flush()

    # 3 ── Users
    user_map = {}
    for login, first, last, dept_code, is_mgr in USERS:
        existing = User.query.filter_by(login_name=login).first()
        if existing:
            user_map[login] = existing
            continue
        u = User(
            employee_no=f"EMP{str(len(user_map) + 1001)}",
            first_name=first,
            last_name=last,
            login_name=login,
            department_id=dept_map[dept_code].id,
            is_manager=is_mgr,
            position_short="manager" if is_mgr else "staff",
        )
        db.session.add(u)
        db.session.flush()
        user_map[login] = u
    print(f"   ✅ {len(user_map)} users ready")

    # 4 ── Spaces
    admin_user = user_map.get("admin") or list(user_map.values())[0]
    space_map = {}
    for name, desc in SPACES:
        existing = Space.query.filter_by(name=name).first()
        if existing:
            space_map[name] = existing
            continue
        s = Space(name=name, description=desc, owner_id=admin_user.id)
        db.session.add(s)
        db.session.flush()
        space_map[name] = s
    print(f"   ✅ {len(space_map)} spaces ready")

    # 5 ── Templates
    template_count = 0
    for tmpl in TEMPLATES:
        existing = Document.query.filter_by(title=tmpl["title"], is_template=True).first()
        if existing:
            template_count += 1
            continue
        doc = Document(
            owner_id=admin_user.id,
            title=tmpl["title"],
            status="approved",
            is_template=True,
            is_public=True,
        )
        db.session.add(doc)
        db.session.flush()

        ver = DocumentVersion(
            document_id=doc.id,
            version_no=1,
            content_json=tmpl["content"],
            created_by_id=admin_user.id,
        )
        db.session.add(ver)
        db.session.flush()
        doc.current_version_id = ver.id
        doc.doc_number = f"TMPL{str(doc.id).zfill(4)}"
        template_count += 1
    print(f"   ✅ {template_count} templates ready")

    # 6 ── Sample Documents (50)
    existing_count = Document.query.filter_by(is_template=False).count()
    if existing_count >= 50:
        print(f"   ✅ {existing_count} sample documents already exist, skipping")
    else:
        users_list = list(user_map.values())
        spaces_list = list(space_map.values())
        statuses = ["draft", "draft", "approved", "approved", "approved", "rejected", "in_approval"]
        from datetime import datetime, timedelta
        import random

        for i, title in enumerate(SAMPLE_TITLES):
            if Document.query.filter_by(title=title, is_template=False).first():
                continue
            owner = users_list[i % len(users_list)]
            space = spaces_list[i % len(spaces_list)] if i % 3 != 0 else None
            status = statuses[i % len(statuses)]
            created_days_ago = random.randint(1, 60)

            doc = Document(
                owner_id=owner.id,
                title=title,
                status=status,
                is_template=False,
                is_public=(status == "approved"),
                space_id=space.id if space else None,
                created_at=datetime.utcnow() - timedelta(days=created_days_ago),
                updated_at=datetime.utcnow() - timedelta(days=max(0, created_days_ago - random.randint(0, 5))),
            )
            db.session.add(doc)
            db.session.flush()

            content = _tiptap_doc(
                title,
                "",
                f"This is a sample document created for demonstration purposes.",
                f"Author: {owner.display_name()}",
                f"Department: {owner.department.name if owner.department else 'N/A'}",
                "",
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            )
            ver = DocumentVersion(
                document_id=doc.id,
                version_no=1,
                content_json=content,
                created_by_id=owner.id,
            )
            db.session.add(ver)
            db.session.flush()
            doc.current_version_id = ver.id
            doc.doc_number = datetime.utcnow().strftime("%Y%m%d") + str(doc.id).zfill(3)

        print(f"   ✅ {len(SAMPLE_TITLES)} sample documents created")

    db.session.commit()
    print("\n🎉 Database seeding completed. System initialized.")
    print("   Login with: admin, zhangwei, lina, wangfang, liuyang, chenxiao, zhaoming, sunli, wugang, zhoujie")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run_seed()
