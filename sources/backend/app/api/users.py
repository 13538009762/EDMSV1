from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import User, Department
from app.utils.auth import current_user
from datetime import datetime

bp = Blueprint("users", __name__)

@bp.get("/stats")
@jwt_required()
def get_stats():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    query = User.query.filter_by(registration_status='active')
    
    if user.login_name != 'admin':
        # Non-admins can only see their own department's stats
        if user.department_id:
            query = query.filter_by(department_id=user.department_id)
        else:
            query = query.filter_by(id=user.id) # Fallback to just themselves if no dept
            
    return jsonify({
        "total_count": query.count(),
        "status": "healthy"
    })

@bp.post("")
@jwt_required()
def create_user():
    admin = current_user()
    if not admin or not admin.is_manager:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    
    # 💡 修改：department_id 对普通经理是可选的，由后端自动填充
    required = ["login_name", "password", "employee_no", "first_name", "last_name"]
    if admin.is_super_admin:
        required.append("department_id")

    for f in required:
        if not data.get(f):
            return jsonify({"error": f"{f} is required"}), 400

    if User.query.filter_by(login_name=data["login_name"]).first():
        return jsonify({"error": "Login name already exists"}), 409
    if User.query.filter_by(employee_no=data["employee_no"]).first():
        return jsonify({"error": "Employee number already exists"}), 409

    user = User(
        employee_no=data["employee_no"],
        login_name=data["login_name"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        patronymic=data.get("patronymic", ""),
        department_id=admin.department_id if not admin.is_super_admin else data["department_id"],
        position_short=data.get("position_short", ""),
        gender=data.get("gender", ""),
        is_manager=data.get("is_manager", False),
        is_super_admin=data.get("is_super_admin", False) if admin.is_super_admin else False,
        registration_status="active"
    )
    user.set_password(data["password"])
    
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created successfully", "user_id": user.id}), 201

@bp.get("/me")
@jwt_required()
def get_me():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "id": user.id,
        "employee_no": user.employee_no,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "patronymic": user.patronymic,
        "login_name": user.login_name,
        "gender": user.gender,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
        "department_id": user.department_id,
        "department_name": user.department.name if user.department else None,
        "department_name_en": user.department.name_en if user.department else None,
        "is_manager": user.is_manager
    })

@bp.get("/me/stats")
@jwt_required()
def get_me_stats():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    from app.models import Document, DocumentVersion, DocumentPermission
    from app.models.workflow import ApprovalFlow, ApprovalParticipant, ApprovalDecision
    from sqlalchemy import or_
    
    # 1. Created docs (owned by user, active, not template)
    created_count = Document.query.filter_by(
        owner_id=user.id, 
        is_template=False, 
        deleted_at=None
    ).count()
    
    # 2. Collaborated docs (not owned by user, but user has explicit permission OR has created a version)
    collab_doc_ids = set()
    
    # a. User has permission
    perms = db.session.query(DocumentPermission.document_id)\
        .filter(DocumentPermission.user_id == user.id).all()
    for p in perms:
        collab_doc_ids.add(p[0])
        
    # b. User has edited/created a version
    versions = db.session.query(DocumentVersion.document_id)\
        .filter(DocumentVersion.created_by_id == user.id).all()
    for v in versions:
        collab_doc_ids.add(v[0])
        
    # Filter valid collaborated documents
    if collab_doc_ids:
        collaborated_count = Document.query.filter(
            Document.id.in_(list(collab_doc_ids)),
            Document.owner_id != user.id,
            Document.deleted_at == None,
            Document.is_template == False
        ).count()
    else:
        collaborated_count = 0
        
    # 3. Approved docs (owned by user that are approved OR approved by this user as reviewer/approver)
    # Documents approved by this user
    reviewed_doc_ids = db.session.query(ApprovalFlow.document_id)\
        .join(ApprovalParticipant, ApprovalParticipant.flow_id == ApprovalFlow.id)\
        .join(ApprovalDecision, ApprovalDecision.participant_id == ApprovalParticipant.id)\
        .filter(ApprovalParticipant.user_id == user.id)\
        .filter(ApprovalDecision.decision == 'approve')\
        .filter(ApprovalFlow.document_id != None)\
        .distinct().all()
        
    approved_doc_ids = [r[0] for r in reviewed_doc_ids]
    
    approved_count = Document.query.filter(
        Document.deleted_at == None,
        Document.is_template == False,
        Document.status == 'approved',
        or_(
            Document.owner_id == user.id,
            Document.id.in_(approved_doc_ids) if approved_doc_ids else False
        )
    ).count()
    
    return jsonify({
        "created_docs": created_count,
        "collaborated_docs": collaborated_count,
        "approved_docs": approved_count
    })


@bp.get("")
@jwt_required()
def list_users():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    query = User.query.filter_by(registration_status='active')
    
    # 逻辑分歧：如果是管理模式 (management=1)，经理只能看本部门
    is_management = request.args.get("management") == "1"
    is_super = user.is_super_admin
    
    if is_management and not is_super and user.is_manager:
        query = query.filter_by(department_id=user.department_id)
    else:
        # 否则允许根据部门 ID 过滤，如果不传则默认查看全部（支持跨部门审批）
        dept_id = request.args.get("department_id")
        if dept_id:
            query = query.filter_by(department_id=dept_id)

    is_mgr = request.args.get("is_manager")
    if is_mgr is not None and is_mgr != "":
        query = query.filter_by(is_manager=bool(int(is_mgr)))

    is_super_adm = request.args.get("is_super_admin")
    if is_super_adm is not None and is_super_adm != "":
        query = query.filter_by(is_super_admin=bool(int(is_super_adm)))

    search = request.args.get("search")

    if search:
        print(f"[DEBUG] User search term: '{search}'")
        s = f"%{search.strip().lower()}%"
        from sqlalchemy import func
        query = query.filter(
            (func.lower(User.first_name).like(s)) | 
            (func.lower(User.last_name).like(s)) |
            (func.lower(User.login_name).like(s)) |
            (func.lower(User.employee_no).like(s)) |
            (func.lower(User.position_short).like(s)) |
            (func.concat(func.lower(User.last_name), func.lower(User.first_name)).like(s)) |
            (func.concat(func.lower(User.last_name), " ", func.lower(User.first_name)).like(s))
        )
    
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 20))
    total = query.count()
    users = query.offset((page - 1) * size).limit(size).all()
    
    items = []
    for u in users:
        items.append({
            "id": u.id,
            "employee_no": u.employee_no,
            "login_name": u.login_name,
            "display_name": u.display_name(),
            "department_id": u.department_id,
            "department_name": u.department.name if u.department else None,
            "department_name_en": u.department.name_en if u.department else None,
            "is_manager": u.is_manager,
            "is_super_admin": u.is_super_admin
        })
    return jsonify({"total": total, "items": items})

@bp.patch("/<int:user_id>")
@jwt_required()
def update_user(user_id: int):
    c_user = current_user()
    target_user = db.session.get(User, user_id)
    if not target_user:
        return jsonify({"error": "User not found"}), 404
    
    is_admin = c_user and (c_user.is_manager or c_user.is_super_admin)
    is_super = c_user and c_user.is_super_admin
    is_self = c_user and c_user.id == target_user.id
    
    # 💡 校验范围：部门经理仅能编辑自己部门的人员
    if not is_super and is_admin:
        if target_user.department_id != c_user.department_id:
            return jsonify({"error": "Forbidden: User belongs to another department"}), 403

    if not is_admin and not is_self:
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json() or {}
    
    # Fields anyone (self or admin) can change
    if "first_name" in data: target_user.first_name = data["first_name"]
    if "last_name" in data: target_user.last_name = data["last_name"]
    if "patronymic" in data: target_user.patronymic = data["patronymic"]
    if "gender" in data: target_user.gender = data["gender"]
    if "birth_date" in data:
        bd_str = data["birth_date"]
        target_user.birth_date = datetime.strptime(bd_str, "%Y-%m-%d").date() if bd_str else None
        
    # Fields ONLY admin can change
    if is_admin:
        # 💡 限制：仅超级管理员（admin）可以修改员工所属部门
        if is_super and "department_id" in data: 
            target_user.department_id = data["department_id"]
        
        if "is_manager" in data: target_user.is_manager = data["is_manager"]
        if "position_short" in data: target_user.position_short = data["position_short"]
        if "login_name" in data:
            new_login = data["login_name"].strip()
            if not new_login:
                return jsonify({"error": "Login name cannot be empty"}), 400
            existing = User.query.filter_by(login_name=new_login).first()
            if existing and existing.id != target_user.id:
                return jsonify({"error": "Login name already exists"}), 409
            target_user.login_name = new_login
        if "is_super_admin" in data:
            if is_self and not data["is_super_admin"]:
                return jsonify({"error": "Cannot revoke your own super admin rights"}), 400
            if is_super:
                target_user.is_super_admin = bool(data["is_super_admin"])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Update failed: {str(e)}"}), 500
    return jsonify({"message": "Updated successfully"})

@bp.delete("/<int:user_id>")
@jwt_required()
def delete_user(user_id: int):
    admin = current_user()
    if not admin or not (admin.is_manager or admin.is_super_admin):
        return jsonify({"error": "Admin access required"}), 403
    
    if admin.id == user_id:
        return jsonify({"error": "Cannot delete yourself"}), 400
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # 💡 范围校验：仅超级管理员可以删除所有人，经理仅能删除本部门人员
    if not admin.is_super_admin and user.department_id != admin.department_id:
        return jsonify({"error": "Forbidden: User is in another department"}), 403
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Cannot delete user (they might have active documents or historical records)"}), 400

@bp.post("/batch-delete")
@jwt_required()
def batch_delete_users():
    admin = current_user()
    if not admin or not (admin.is_manager or admin.is_super_admin):
        return jsonify({"error": "Admin access required"}), 403
    
    data = request.get_json() or {}
    user_ids = data.get("user_ids", [])
    if not user_ids:
        return jsonify({"error": "No user IDs provided"}), 400
    
    # Filter out current admin to prevent self-deletion
    user_ids = [uid for uid in user_ids if uid != admin.id]
    
    deleted_count = 0
    errors = []
    
    for uid in user_ids:
        u = db.session.get(User, uid)
        if u:
            # 💡 优化：对于部门经理，跳过不属于其部门的用户
            if not admin.is_super_admin and u.department_id != admin.department_id:
                errors.append(f"User ID {uid} belongs to another department - skipped")
                continue
            
            try:
                db.session.delete(u)
                deleted_count += 1
            except Exception:
                errors.append(f"User ID {uid} could not be deleted (constraints)")
    
    db.session.commit()
    return jsonify({"message": f"Deleted {deleted_count} users", "errors": errors})

@bp.get("/departments")
@jwt_required(optional=True)
def list_depts():
    # 允许所有人查看所有部门列表，以便发起跨部门审批
    depts = Department.query.all()
    return jsonify([{"id": d.id, "name": d.name, "name_en": d.name_en} for d in depts])

@bp.post("/departments")
@jwt_required()
def create_department():
    admin = current_user()
    if not admin or not admin.is_super_admin:
        return jsonify({"error": "Strict admin access required"}), 403
    
    data = request.get_json() or {}
    name = data.get("name")
    name_en = data.get("name_en")
    if not name:
        return jsonify({"error": "Department name is required"}), 400
    
    if Department.query.filter_by(name=name).first():
        return jsonify({"error": "Department already exists"}), 409
    
    dept = Department(name=name, name_en=name_en, code=f"DEPT_{name}")
    db.session.add(dept)
    db.session.commit()
    return jsonify({"id": dept.id, "name": dept.name, "name_en": dept.name_en}), 201

@bp.post("/<int:user_id>/reset-password")
@jwt_required()
def reset_password(user_id: int):
    admin = current_user()
    if not admin or not (admin.is_manager or admin.is_super_admin):
        return jsonify({"error": "Admin access required"}), 403
        
    target_user = db.session.get(User, user_id)
    if not target_user:
        return jsonify({"error": "User not found"}), 404
        
    # 💡 范围校验：部门经理仅能重置本部门人员密码
    if not admin.is_super_admin and target_user.department_id != admin.department_id:
        return jsonify({"error": "Forbidden: User belongs to another department"}), 403
        
    data = request.get_json(silent=True) or {}
    new_password = data.get("password")
    if not new_password:
        return jsonify({"error": "New password is required"}), 400
        
    try:
        target_user.set_password(new_password)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Reset failed: {str(e)}"}), 500
        
    return jsonify({"message": "Password reset successfully"})

@bp.get("/org")
@jwt_required()
def get_org():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Manager
    manager = None
    if user.manager_employee_no:
        manager_user = User.query.filter_by(employee_no=user.manager_employee_no).first()
        if manager_user:
            manager = {
                "id": manager_user.id,
                "display_name": manager_user.display_name(),
                "position": manager_user.position_short,
                "login_name": manager_user.login_name,
                "is_manager": manager_user.is_manager
            }
            
    # Peers (same department, excluding self)
    peers = []
    if user.department_id:
        peer_users = User.query.filter(
            User.department_id == user.department_id,
            User.id != user.id,
            User.registration_status == 'active'
        ).limit(15).all()
        for p in peer_users:
            peers.append({
                "id": p.id,
                "display_name": p.display_name(),
                "position": p.position_short,
                "login_name": p.login_name,
                "is_manager": p.is_manager
            })
            
    return jsonify({
        "manager": manager,
        "peers": peers,
        "department": user.department.name if user.department else "未分配部门"
    })
