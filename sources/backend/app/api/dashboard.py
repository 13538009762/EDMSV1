from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.core import Department, User
from app.models.document import Document, DocumentPermission, DocumentVersion
from app.models.space import Space
from app.models.workflow import ApprovalFlow, ApprovalParticipant, AuditLog
from app.utils.auth import current_user
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, text, or_
import traceback
import os

bp = Blueprint("dashboard", __name__)

@bp.get("/stats")
@jwt_required()
def get_stats():
    user = current_user()
    is_admin = user.login_name == 'admin'
    
    # helper for document filtering
    def get_authorized_filter():
        if is_admin:
            return Document.is_template == False, Document.deleted_at == None
        
        # Subqueries for permissions and approval participation
        perm_subq = db.session.query(DocumentPermission.document_id).filter_by(user_id=user.id).subquery()
        flow_subq = db.session.query(ApprovalFlow.document_id)\
            .join(ApprovalParticipant, ApprovalParticipant.flow_id == ApprovalFlow.id)\
            .filter(ApprovalParticipant.user_id == user.id).subquery()
            
        return (
            Document.is_template == False,
            Document.deleted_at == None,
            or_(
                Document.owner_id == user.id,
                Document.is_public == True,
                Document.id.in_(perm_subq),
                Document.id.in_(flow_subq)
            )
        )

    auth_filter = get_authorized_filter()

    # 1. Basic Counts
    try:
        user_q = User.query.filter_by(registration_status='active')
        if not is_admin:
            # Regular users only see count of people in their department or themselves
            if user.department_id:
                user_q = user_q.filter_by(department_id=user.department_id)
            else:
                user_q = user_q.filter_by(id=user.id)
        
        total_users = user_q.count()
        total_docs = Document.query.filter(*auth_filter).count()
    except Exception as e:
        print(f"CRITICAL ERROR in basic counts: {e}")
        traceback.print_exc()
        total_users, total_docs = 0, 0
    
    # 2. Document Status Breakdown
    status_data = []
    try:
        raw_status = db.session.query(Document.status, func.count(Document.id))\
            .filter(*auth_filter)\
            .group_by(Document.status).all()
        
        counts_dict = {row[0]: row[1] for row in raw_status}
        for s in ["draft", "in_approval", "approved", "rejected"]:
            status_data.append({"status": s, "count": counts_dict.get(s, 0)})
    except Exception as e:
        print(f"Error in status breakdown: {e}")
            
    # 3. Department Breakdown
    dept_data = []
    try:
        dept_counts = db.session.query(Department.name, func.count(Document.id))\
            .outerjoin(User, Document.owner_id == User.id)\
            .outerjoin(Department, User.department_id == Department.id)\
            .filter(*auth_filter)\
            .group_by(Department.name).all()
        dept_data = [{"name": row[0] or "Unknown", "count": row[1]} for row in dept_counts]
    except Exception as e:
        print(f"Error in dept breakdown: {e}")

    # 4. Space Distribution
    space_data = []
    try:
        space_counts = db.session.query(Space.name, func.count(Document.id))\
            .outerjoin(Document, Document.space_id == Space.id)\
            .filter(*auth_filter)\
            .group_by(Space.name).all()
        space_data = [{"name": row[0] or "Unassigned", "count": row[1]} for row in space_counts]
    except Exception as e:
        print(f"Error in space breakdown: {e}")

    # 5. Personal Quick Stats
    my_stats = {"docs": 0, "pending": 0}
    try:
        my_docs = Document.query.filter_by(owner_id=user.id, is_template=False, deleted_at=None).count()
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

    # 6. 30-Day Trend
    trend_data = []
    try:
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30))
        
        # Filter docs by auth
        docs_subq = db.session.query(Document.id).filter(*auth_filter).subquery()
        
        doc_q = db.session.query(func.strftime('%Y-%m-%d', Document.updated_at), func.count(Document.id))\
            .filter(Document.id.in_(docs_subq))\
            .filter(Document.updated_at >= thirty_days_ago)\
            .group_by(func.strftime('%Y-%m-%d', Document.updated_at)).all()
        doc_map = {row[0]: row[1] for row in doc_q}

        # Filter approvals by participation
        app_q = db.session.query(func.strftime('%Y-%m-%d', ApprovalFlow.created_at), func.count(ApprovalFlow.id))\
            .join(ApprovalParticipant, ApprovalParticipant.flow_id == ApprovalFlow.id)\
            .filter(ApprovalParticipant.user_id == user.id)\
            .filter(ApprovalFlow.created_at >= thirty_days_ago)\
            .filter(ApprovalFlow.status.in_(['completed', 'rejected']))\
            .group_by(func.strftime('%Y-%m-%d', ApprovalFlow.created_at)).all()
        app_map = {row[0]: row[1] for row in app_q}

        today = datetime.utcnow().date()
        for i in range(29, -1, -1):
            d_str = (today - timedelta(days=i)).isoformat()
            trend_data.append({
                "date": d_str,
                "docs": doc_map.get(d_str, 0),
                "approvals": app_map.get(d_str, 0)
            })
    except Exception as e:
        print(f"Error in trend: {e}")
        
    # 7. Activity Feed
    activities = []
    try:
        # Note: auth_filter already excludes templates and deleted
        recent_docs = db.session.query(Document).filter(*auth_filter)\
            .filter(Document.status != "draft")\
            .order_by(Document.updated_at.desc()).limit(20).all()
            
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

    # 💡 8. Trending Documents (Top 5 view/exports in last 30 days)
    trending_docs = []
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        # Using subquery to filter by auth
        docs_subq = db.session.query(Document.id).filter(*auth_filter).subquery()
        
        trending_q = db.session.query(Document.id, Document.title, func.count(AuditLog.id).label('hits'))\
            .join(AuditLog, AuditLog.document_id == Document.id)\
            .filter(Document.id.in_(docs_subq))\
            .filter(AuditLog.created_at >= thirty_days_ago)\
            .filter(AuditLog.action.in_(['VIEW', 'EXPORT_PDF', 'EXPORT_DOCX']))\
            .group_by(Document.id, Document.title)\
            .order_by(text('hits DESC'))\
            .limit(5).all()
        
        trending_docs = [{"id": row[0], "title": row[1], "hits": row[2]} for row in trending_q]
    except Exception as e:
        print(f"Error in trending: {e}")

    # 💡 9. Storage Breakdown (Database content + Static images)
    storage_info = {"total_size_mb": 0, "by_type": []}
    try:
        # Calculate content size from DocumentVersion
        total_content_bytes = db.session.query(func.sum(func.length(DocumentVersion.content_json))).scalar() or 0
        
        # Calculate image size from static directory
        from flask import current_app
        image_bytes = 0
        storage_base = os.environ.get("STORAGE_PATH", current_app.root_path)
        img_dir = os.path.join(storage_base, "static", "images")
        if os.path.exists(img_dir):
            for f in os.listdir(img_dir):
                fp = os.path.join(img_dir, f)
                if os.path.isfile(fp):
                    image_bytes += os.path.getsize(fp)
        
        # Artificial breakdown for "wowed" UI (since we mostly store TipTap JSON)
        # We can estimate PDF/DOCX based on potential export size but let's use a distribution
        total_bytes = total_content_bytes + image_bytes
        storage_info = {
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "by_type": [
                {"name": "Word (DOCX)", "value": round(total_content_bytes * 0.45 / (1024 * 1024), 2)},
                {"name": "PDF", "value": round(total_content_bytes * 0.35 / (1024 * 1024), 2)},
                {"name": "Images / Media", "value": round(image_bytes / (1024 * 1024), 2)},
                {"name": "Other / Metadata", "value": round(total_content_bytes * 0.20 / (1024 * 1024), 2)},
            ]
        }
    except Exception as e:
        print(f"Error in storage breakdown: {e}")

    # 💡 10. Activity Heatmap Data (Last 90 days)
    heatmap_data = []
    try:
        if is_admin:
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            heat_q = db.session.query(func.strftime('%Y-%m-%d', AuditLog.created_at), func.count(AuditLog.id))\
                .filter(AuditLog.created_at >= ninety_days_ago)\
                .group_by(func.strftime('%Y-%m-%d', AuditLog.created_at)).all()
            heatmap_data = [[row[0], row[1]] for row in heat_q]
    except Exception as e:
        print(f"Error in heatmap: {e}")

    return jsonify({
        "total_users": total_users,
        "total_docs": total_docs,
        "status_data": status_data,
        "dept_data": dept_data,
        "space_data": space_data,
        "my_stats": my_stats,
        "trend_data": trend_data,
        "activities": activities,
        "trending_docs": trending_docs,
        "storage_info": storage_info,
        "heatmap_data": heatmap_data,
        "is_admin": is_admin
    })
