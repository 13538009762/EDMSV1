from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required

from app.models import User
from app.utils.auth import current_user

bp = Blueprint("auth", __name__)


@bp.post("/login")
def login():
    """Login with login_name and password."""
    data = request.get_json(silent=True) or {}
    login_name = (data.get("login_name") or "").strip()
    password = data.get("password") or ""
    
    if not login_name:
        return jsonify({"error": "login_name required"}), 400
        
    user = User.query.filter_by(login_name=login_name).first()
    if not user:
        return jsonify({"error": "Invalid login"}), 401
    
    if user.registration_status != "active":
        status_map = {
            "pending_dept": "Pending department approval",
            "pending_admin": "Pending admin approval",
            "rejected": "Your registration was rejected"
        }
        return jsonify({"error": status_map.get(user.registration_status, "Account inactive")}), 403

    if not user.check_password(password):
        return jsonify({"error": "Invalid password"}), 401
        
    token = create_access_token(identity=str(user.id))
    return jsonify(
        {
            "access_token": token,
            "user": {
                "id": user.id,
                "login_name": user.login_name,
                "display_name": user.display_name(),
                "employee_no": user.employee_no,
                "is_manager": user.is_manager,
            },
        }
    )

@bp.post("/register")
def register():
    from app.extensions import db
    data = request.get_json(silent=True) or {}
    
    required = ["login_name", "password", "first_name", "last_name", "department_id"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"{f} is required"}), 400

    if User.query.filter_by(login_name=data["login_name"]).first():
        return jsonify({"error": "Login name already exists"}), 409

    user = User(
        login_name=data["login_name"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        employee_no=f"REQ_{data['login_name']}", # Temp ID
        department_id=data["department_id"],
        registration_status="pending_dept"
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush() # Get user.id

    # Registration Flow Logic will be implemented in a service or handled here
    # For now, we save the user and create the flow
    try:
        from app.models.workflow import ApprovalFlow, ApprovalParticipant
        # Step 1: Dept Manager
        flow = ApprovalFlow(document_id=None, flow_type="registration", status="active")
        flow.rel_id = user.id # Link to user
        db.session.add(flow)
        db.session.flush()

        # We'll need a way to find the manager of the department
        # Step 1: All HR Managers (OR condition: any one passes)
        from app.models.core import Department
        hr_dept = Department.query.filter(Department.name.like("%Human Resources%")).first()
        hr_managers = []
        if hr_dept:
            hr_managers = User.query.filter_by(department_id=hr_dept.id, is_manager=True).all()
        
        # If no HR managers found, use any system manager as fallback
        if not hr_managers:
            hr_managers = User.query.filter_by(is_manager=True).limit(1).all()

        for mgr in hr_managers:
            part = ApprovalParticipant(flow_id=flow.id, user_id=mgr.id, step_order=1)
            db.session.add(part)

        # Step 2: System Admin (Final Activation)
        admin_user = User.query.filter_by(login_name="admin").first() 
        if not admin_user: # Fallback to first manager
            admin_user = User.query.filter_by(is_manager=True).first()
            
        if admin_user:
            part2 = ApprovalParticipant(flow_id=flow.id, user_id=admin_user.id, step_order=2)
            db.session.add(part2)
            
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed during flow creation: {str(e)}"}), 500

    return jsonify({"message": "Registration submitted. Waiting for approval."}), 201


@bp.get("/me")
@jwt_required()
def me():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(
        {
            "id": user.id,
            "login_name": user.login_name,
            "display_name": user.display_name(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "employee_no": user.employee_no,
            "is_manager": user.is_manager,
            "department": {
                "id": user.department.id if user.department else None,
                "name": user.department.name if user.department else "",
                "name_en": user.department.name_en if user.department else ""
            } if user.department else None,
            "position": user.position_short
        }
    )


@bp.post("/change-password")
@jwt_required()
def change_password():
    from app.extensions import db
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    
    if not old_password or not new_password:
        return jsonify({"error": "Current and new passwords are required"}), 400
        
    if not user.check_password(old_password):
        return jsonify({"error": "Invalid current password"}), 401
        
    try:
        user.set_password(new_password)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Update failed: {str(e)}"}), 500
    
    return jsonify({"message": "Password updated successfully"})
