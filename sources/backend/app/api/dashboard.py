from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.core import Department, User
from app.models.document import Document
from app.models.space import Space
from app.utils.auth import current_user
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, text
import traceback

bp = Blueprint("dashboard", __name__)

@bp.get("/stats")
@jwt_required()
def get_stats():
    # Basic fail-safe counts (No complex filters initially)
    try:
        total_users = User.query.filter_by(registration_status='active').count()
        total_docs = Document.query.filter_by(is_template=False, deleted_at=None).count()
    except Exception as e:
        print(f"CRITICAL ERROR in basic counts: {e}")
        traceback.print_exc()
        total_users, total_docs = 0, 0
    
    # 2. Document Status Breakdown
    status_data = []
    try:
        # Avoid complex query if possible
        raw_status = db.session.query(Document.status, func.count(Document.id)).filter(
            Document.is_template == False,
            Document.deleted_at == None
        ).group_by(Document.status).all()
        
        counts_dict = {row[0]: row[1] for row in raw_status}
        for s in ["draft", "in_approval", "approved", "rejected"]:
            status_data.append({"status": s, "count": counts_dict.get(s, 0)})
    except Exception as e:
        print(f"Error in status breakdown: {e}")
        traceback.print_exc()
            
    # 3. Department Breakdown
    dept_data = []
    try:
        dept_counts = db.session.query(Department.name, func.count(Document.id))\
            .outerjoin(User, Document.owner_id == User.id)\
            .outerjoin(Department, User.department_id == Department.id)\
            .filter(Document.is_template == False, Document.deleted_at == None)\
            .group_by(Department.name).all()
        dept_data = [{"name": row[0] or "Unknown", "count": row[1]} for row in dept_counts]
    except Exception as e:
        print(f"Error in dept breakdown: {e}")

    # 4. Space Distribution
    space_data = []
    try:
        space_counts = db.session.query(Space.name, func.count(Document.id))\
            .outerjoin(Document, Document.space_id == Space.id)\
            .filter(Document.is_template == False, Document.deleted_at == None)\
            .group_by(Space.name).all()
        space_data = [{"name": row[0] or "Unassigned", "count": row[1]} for row in space_counts]
    except Exception as e:
        print(f"Error in space breakdown: {e}")

    # 5. Personal Quick Stats
    my_stats = {"docs": 0, "pending": 0}
    try:
        user = current_user()
        my_docs = Document.query.filter_by(owner_id=user.id, is_template=False, deleted_at=None).count()
        # Correctly count pending approvals where it is actually MY turn
        my_pending_row = db.session.execute(
            text("""
                SELECT COUNT(*) FROM approval_flows af
                JOIN approval_participants ap ON ap.flow_id = af.id
                LEFT JOIN approval_decisions ad ON ad.participant_id = ap.id
                WHERE ap.user_id = :uid 
                  AND af.status = 'active'
                  AND ad.id IS NULL
                  AND (af.flow_type != 'sequential' OR ap.step_order = af.current_order)
            """), {"uid": user.id}
        ).scalar()
        my_stats = {"docs": my_docs, "pending": my_pending_row or 0}
    except Exception as e:
        print(f"Error in personal stats: {e}")
        traceback.print_exc()

    # 6. 30-Day Trend (Raw SQL to avoid ORM column issues)
    trend_data = []
    try:
        today = datetime.utcnow().date()
        for i in range(29, -1, -1):
            target_date = today - timedelta(days=i)
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())

            doc_count = db.session.execute(
                text("SELECT COUNT(*) FROM documents WHERE updated_at >= :s AND updated_at <= :e AND is_template = 0 AND deleted_at IS NULL"),
                {"s": start_dt, "e": end_dt}
            ).scalar() or 0

            approval_count = db.session.execute(
                text("SELECT COUNT(*) FROM approval_flows WHERE created_at >= :s AND created_at <= :e AND status IN ('approved', 'rejected')"),
                {"s": start_dt, "e": end_dt}
            ).scalar() or 0

            trend_data.append({
                "date": target_date.isoformat(),
                "docs": doc_count,
                "approvals": approval_count
            })
    except Exception as e:
        print(f"Error in trend: {e}")
        traceback.print_exc()
        
    # 7. Activity Feed
    activities = []
    try:
        recent_docs = db.session.query(Document).filter(
            Document.status != "draft",
            Document.is_template == False,
            Document.deleted_at == None
        ).order_by(Document.updated_at.desc()).limit(20).all()
        for doc in recent_docs:
            activities.append({
                "id": doc.id,
                "title": doc.title,
                "status": doc.status,
                "updated_at": doc.updated_at.isoformat() + "Z" if doc.updated_at else None,
                "owner_name": doc.owner.display_name() if doc.owner else "Unknown"
            })
    except Exception as e:
        print(f"Error in activities: {e}")
        traceback.print_exc()

    return jsonify({
        "total_users": total_users,
        "total_docs": total_docs,
        "status_data": status_data,
        "dept_data": dept_data,
        "space_data": space_data,
        "my_stats": my_stats,
        "trend_data": trend_data,
        "activities": activities
    })
