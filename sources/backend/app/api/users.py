from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import User, Department
from app.utils.auth import current_user
from datetime import datetime

bp = Blueprint("users", __name__)

@bp.post("")
@jwt_required()
def create_user():
    admin = current_user()
    if not admin or not admin.is_manager:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    required = ["login_name", "password", "employee_no", "first_name", "last_name", "department_id"]
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
        department_id=data["department_id"],
        position_short=data.get("position_short", ""),
        gender=data.get("gender", ""),
        is_manager=data.get("is_manager", False),
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

@bp.get("")
@jwt_required()
def list_users():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    query = User.query.filter_by(registration_status='active')
    search = request.args.get("search")

    if search:
        s = f"%{search}%"
        query = query.filter(
            (User.first_name.like(s)) | 
            (User.last_name.like(s)) |
            (User.login_name.like(s)) |
            (User.employee_no.like(s)) |
            (User.position_short.like(s))
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
            "is_manager": u.is_manager
        })
    return jsonify({"total": total, "items": items})

@bp.patch("/<int:user_id>")
@jwt_required()
def update_user(user_id: int):
    c_user = current_user()
    target_user = db.session.get(User, user_id)
    if not target_user:
        return jsonify({"error": "User not found"}), 404
    
    is_admin = c_user and c_user.is_manager
    is_self = c_user and c_user.id == target_user.id
    
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
        if "department_id" in data: target_user.department_id = data["department_id"]
        if "is_manager" in data: target_user.is_manager = data["is_manager"]
        if "position_short" in data: target_user.position_short = data["position_short"]

    db.session.commit()
    return jsonify({"message": "Updated successfully"})

@bp.delete("/<int:user_id>")
@jwt_required()
def delete_user(user_id: int):
    admin = current_user()
    if not admin or not admin.is_manager:
        return jsonify({"error": "Admin access required"}), 403
    
    if admin.id == user_id:
        return jsonify({"error": "Cannot delete yourself"}), 400
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
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
    if not admin or not admin.is_manager:
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
            try:
                db.session.delete(u)
                deleted_count += 1
            except Exception:
                errors.append(f"User ID {uid} could not be deleted (constraints)")
    
    db.session.commit()
    return jsonify({"message": f"Deleted {deleted_count} users", "errors": errors})

@bp.get("/departments")
def list_depts():
    depts = Department.query.all()
    return jsonify([{"id": d.id, "name": d.name, "name_en": d.name_en} for d in depts])

@bp.post("/departments")
@jwt_required()
def create_department():
    admin = current_user()
    if not admin or admin.login_name != "admin":
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
