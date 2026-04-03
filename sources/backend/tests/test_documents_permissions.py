"""文档状态机与权限 API 行为测试。"""
from app.extensions import db
from app.models import Department, Document, DocumentPermission, DocumentVersion, User


def _token(client, app, login_name: str) -> str:
    with app.app_context():
        if not User.query.filter_by(login_name=login_name).first():
            code = f"dept-{login_name}"
            d = Department.query.filter_by(code=code).first()
            if not d:
                d = Department(code=code, name="Test Dept")
                db.session.add(d)
                db.session.flush()
            u = User(
                employee_no=f"e-{login_name}",
                last_name="A",
                first_name="B",
                login_name=login_name,
                department_id=d.id,
            )
            db.session.add(u)
            db.session.commit()
    r = client.post("/api/auth/login", json={"login_name": login_name})
    assert r.status_code == 200, r.get_json()
    return r.get_json()["access_token"]


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_title_patch_requires_editor_not_viewer(client, app):
    with app.app_context():
        ddept = Department(code="1", name="X")
        db.session.add(ddept)
        db.session.flush()
        owner = User(
            employee_no="o",
            last_name="O",
            first_name="w",
            login_name="owner1",
            department_id=ddept.id,
        )
        viewer = User(
            employee_no="v",
            last_name="V",
            first_name="w",
            login_name="viewer1",
            department_id=ddept.id,
        )
        db.session.add_all([owner, viewer])
        db.session.flush()
        doc = Document(owner_id=owner.id, title="T", status="draft")
        db.session.add(doc)
        db.session.flush()
        ver = DocumentVersion(
            document_id=doc.id,
            version_no=1,
            content_json=DocumentVersion.default_content_json(),
            created_by_id=owner.id,
        )
        db.session.add(ver)
        db.session.flush()
        doc.current_version_id = ver.id
        db.session.add(
            DocumentPermission(document_id=doc.id, user_id=viewer.id, role="view")
        )
        db.session.commit()
        doc_id = doc.id

    tok_v = _token(client, app, "viewer1")
    r = client.patch(
        f"/api/documents/{doc_id}",
        json={"title": "Hacked"},
        headers=_auth_headers(tok_v),
    )
    assert r.status_code == 403

    tok_o = _token(client, app, "owner1")
    r = client.patch(
        f"/api/documents/{doc_id}",
        json={"title": "OK"},
        headers=_auth_headers(tok_o),
    )
    assert r.status_code == 200
    assert r.get_json()["title"] == "OK"


def test_permissions_only_draft(client, app):
    with app.app_context():
        ddept = Department(code="1", name="X")
        db.session.add(ddept)
        db.session.flush()
        owner = User(
            employee_no="o",
            last_name="O",
            first_name="w",
            login_name="own2",
            department_id=ddept.id,
        )
        other = User(
            employee_no="x",
            last_name="X",
            first_name="y",
            login_name="oth2",
            department_id=ddept.id,
        )
        db.session.add_all([owner, other])
        db.session.flush()
        doc = Document(owner_id=owner.id, title="T", status="in_approval")
        db.session.add(doc)
        db.session.flush()
        ver = DocumentVersion(
            document_id=doc.id,
            version_no=1,
            content_json=DocumentVersion.default_content_json(),
        )
        db.session.add(ver)
        db.session.flush()
        doc.current_version_id = ver.id
        db.session.commit()
        did = doc.id
        oid = other.id

    tok = _token(client, app, "own2")
    r = client.post(
        f"/api/documents/{did}/permissions",
        json={"grants": [{"user_id": oid, "role": "view"}]},
        headers=_auth_headers(tok),
    )
    assert r.status_code == 400


def test_list_status_filter(client, app):
    with app.app_context():
        ddept = Department(code="1", name="X")
        db.session.add(ddept)
        db.session.flush()
        u = User(
            employee_no="u",
            last_name="U",
            first_name="u",
            login_name="usr3",
            department_id=ddept.id,
        )
        db.session.add(u)
        db.session.flush()
        for st in ("draft", "approved"):
            d = Document(owner_id=u.id, title=st, status=st)
            db.session.add(d)
            db.session.flush()
            v = DocumentVersion(
                document_id=d.id,
                version_no=1,
                content_json=DocumentVersion.default_content_json(),
            )
            db.session.add(v)
            db.session.flush()
            d.current_version_id = v.id
        db.session.commit()

    tok = _token(client, app, "usr3")
    r = client.get("/api/documents", query_string={"scope": "mine", "status": "draft"}, headers=_auth_headers(tok))
    assert r.status_code == 200
    items = r.get_json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "draft"
