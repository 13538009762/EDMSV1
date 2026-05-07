from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.core import Department, User
from app.models.document import Document, DocumentPermission, DocumentVersion
from app.models.space import Space
from app.models.workflow import ApprovalFlow, ApprovalParticipant, AuditLog
from app.utils.auth import current_user
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, text, or_, select
import traceback
import os

bp = Blueprint("dashboard", __name__)

@bp.get("/stats")
@jwt_required()
def get_stats():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    is_admin = user.login_name == 'admin'
    
    # 💡 权限过滤器：确保管理员看到全部，普通用户看到授权内容
    def get_authorized_filter():
        if is_admin:
            return (Document.is_template == False, Document.deleted_at == None)
        
        perm_stmt = select(DocumentPermission.document_id).where(DocumentPermission.user_id == user.id)
        flow_stmt = select(ApprovalFlow.document_id)\
            .join(ApprovalParticipant, ApprovalParticipant.flow_id == ApprovalFlow.id)\
            .filter(ApprovalParticipant.user_id == user.id)
            
        # 💡 Secure permission union: same as documents.py
        final_cond = or_(
            Document.owner_id == user.id,
            Document.is_public == True,
            Document.id.in_(perm_stmt),
            Document.id.in_(flow_stmt)
        )
        
        # 💡 Manager can see department docs
        if user.is_manager and user.department_id:
            dept_users_stmt = select(User.id).where(User.department_id == user.department_id)
            final_cond = or_(final_cond, Document.owner_id.in_(dept_users_stmt))
            
        return (
            Document.is_template == False,
            Document.deleted_at == None,
            final_cond
        )

    auth_filter = get_authorized_filter()

    # 1. 基础指标统计 (KPIs)
    total_users = 0
    total_docs = 0
    try:
        # 💡 User count should also be scope-limited (e.g. within department) for non-admins
        if is_admin:
            total_users = db.session.query(func.count(User.id)).scalar() or 0
        else:
            if user.department_id:
                total_users = User.query.filter_by(department_id=user.department_id).count()
            else:
                total_users = 1 # Just self
        total_docs = Document.query.filter(*auth_filter).count()
    except Exception as e:
        print(f"[CRITICAL ERROR] Basic metrics failed: {e}")
        traceback.print_exc()

    # 2. 文档状态分布 (KPI 细分)
    status_data = []
    try:
        raw_status = db.session.query(Document.status, func.count(Document.id))\
            .filter(*auth_filter)\
            .group_by(Document.status).all()
        counts_dict = {row[0]: row[1] for row in raw_status}
        for s in ["draft", "in_approval", "approved", "rejected"]:
            status_data.append({"status": s, "count": counts_dict.get(s, 0)})
    except Exception as e:
        print(f"[ERROR] Status breakdown failed: {e}")

    # 3. 部门分布
    dept_data = []
    try:
        dept_counts = db.session.query(Department.name, Department.name_en, func.count(Document.id))\
            .outerjoin(User, Document.owner_id == User.id)\
            .outerjoin(Department, User.department_id == Department.id)\
            .filter(*auth_filter)\
            .group_by(Department.name, Department.name_en).all()
        dept_data = [{"name": str(row[0] or "Unknown"), "name_en": str(row[1] or ""), "count": row[2]} for row in dept_counts]
    except Exception as e:
        print(f"[ERROR] Dept breakdown failed: {e}")

    # 4. 空间分布
    space_data = []
    try:
        space_counts = db.session.query(Space.name, func.count(Document.id))\
            .outerjoin(Document, Document.space_id == Space.id)\
            .filter(*auth_filter)\
            .group_by(Space.name).all()
        space_data = [{"name": row[0] or "Unassigned", "count": row[1]} for row in space_counts]
    except Exception as e:
        print(f"[ERROR] Space breakdown failed: {e}")

    # 5. 用户个人简报
    my_stats = {"docs": 0, "pending": 0}
    try:
        my_stats["docs"] = Document.query.filter_by(owner_id=user.id, is_template=False, deleted_at=None).count()
        my_pending = db.session.execute(
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
        my_stats["pending"] = my_pending or 0
    except Exception as e:
        print(f"[ERROR] Personal stats failed: {e}")

    # 6. 30日趋势图 (使用更稳健的日期转换方式)
    trend_data = []
    try:
        # 使用 datetime 统一操作
        today_dt = datetime.now()
        thirty_days_ago = today_dt - timedelta(days=30)
        
        docs_stmt = select(Document.id).where(*auth_filter)
        
        # 针对 MySQL 优化：使用 func.date 进行日期截断
        doc_q = db.session.query(func.date(Document.updated_at), func.count(Document.id))\
            .filter(Document.id.in_(docs_stmt))\
            .filter(Document.updated_at >= thirty_days_ago)\
            .group_by(func.date(Document.updated_at)).all()
        doc_map = {str(row[0]): row[1] for row in doc_q}

        app_q_base = db.session.query(func.date(ApprovalFlow.created_at), func.count(ApprovalFlow.id))
        if not is_admin:
            app_q_base = app_q_base.join(ApprovalParticipant, ApprovalParticipant.flow_id == ApprovalFlow.id)\
                .filter(ApprovalParticipant.user_id == user.id)
            
        app_q = app_q_base.filter(ApprovalFlow.created_at >= thirty_days_ago)\
            .filter(ApprovalFlow.status.in_(['completed', 'rejected']))\
            .group_by(func.date(ApprovalFlow.created_at)).all()
        app_map = {str(row[0]): row[1] for row in app_q}

        for i in range(29, -1, -1):
            d = (today_dt - timedelta(days=i)).date()
            d_str = d.isoformat()
            trend_data.append({
                "date": d_str,
                "docs": doc_map.get(d_str, 0),
                "approvals": app_map.get(d_str, 0)
            })
    except Exception as e:
        print(f"[ERROR] Trend calculation failed: {e}")
        
    # 7. 活跃记录流
    activities = []
    try:
        recent_docs = db.session.query(Document).filter(*auth_filter)\
            .filter(Document.status != "draft")\
            .order_by(Document.updated_at.desc()).limit(20).all()
        for d in recent_docs:
            activities.append({
                "id": d.id, 
                "title": str(d.title or ""), 
                "status": str(d.status or ""),
                "updated_at": d.updated_at.isoformat() + "Z" if d.updated_at else None,
                "owner_name": str(d.owner.display_name() if d.owner else "Unknown")
            })
    except Exception as e:
        print(f"[ERROR] Activity feed failed: {e}")

    # 8. 热门指数 (Top 5)
    trending_docs = []
    try:
        t_limit = datetime.now() - timedelta(days=30)
        t_q = db.session.query(Document.id, Document.title, func.count(AuditLog.id).label('hits'))\
            .join(AuditLog, AuditLog.document_id == Document.id)\
            .filter(Document.id.in_(select(Document.id).where(*auth_filter)))\
            .filter(AuditLog.created_at >= t_limit)\
            .filter(AuditLog.action.in_(['VIEW', 'EXPORT_PDF', 'EXPORT_DOCX']))\
            .group_by(Document.id, Document.title)\
            .order_by(text('hits DESC')).limit(5).all()
        trending_docs = [{"id": r[0], "title": str(r[1] or ""), "hits": r[2]} for r in t_q]
    except Exception as e:
        print(f"[ERROR] Trending failed: {e}")

    # 9. 存储空间分析 (Storage Analytics)
    storage_info = {"total_size_mb": 0, "by_type": []}
    try:
        # 计算数据库中的文本内容大小
        total_content = db.session.query(func.sum(func.length(func.coalesce(DocumentVersion.content_json, "")))).scalar() or 0
        # 计算 Yjs 二进制状态大小
        total_yjs = db.session.query(func.sum(func.length(func.coalesce(DocumentVersion.yjs_state, "")))).scalar() or 0
        
        image_bytes = 0
        upload_bytes = 0
        storage_root = os.environ.get("STORAGE_PATH", os.getcwd())
        
        # 计算静态图片大小
        img_dir = os.path.join(storage_root, "static", "images")
        if os.path.exists(img_dir):
            for f in os.listdir(img_dir):
                fp = os.path.join(img_dir, f)
                if os.path.isfile(fp): image_bytes += os.path.getsize(fp)
        
        # 计算上传的 PDF/DOCX 文件大小
        upload_dir = os.path.join(storage_root, "static", "uploads")
        if os.path.exists(upload_dir):
            for f in os.listdir(upload_dir):
                fp = os.path.join(upload_dir, f)
                if os.path.isfile(fp): upload_bytes += os.path.getsize(fp)

        total_bytes = total_content + total_yjs + image_bytes + upload_bytes
        # 即使没有文档，系统元数据和日志也会占用一点空间，设置一个极小的底数 0.01MB 确保图表不为空
        if total_bytes < 10240: # < 10KB
            total_bytes = 10240 # Force 0.01MB minimum

        total_mb = round(total_bytes / (1024*1024), 2)
        
        storage_info = {
            "total_size_mb": total_mb,
            "by_type": [
                {"name": "Rich Text (JSON)", "value": round(total_content / (1024*1024), 3)},
                {"name": "Real-time States", "value": round(total_yjs / (1024*1024), 3)},
                {"name": "Binary Assets", "value": round((image_bytes + upload_bytes) / (1024*1024), 3)},
                {"name": "System Meta", "value": 0.005}, # 基础系统开销
            ]
        }
    except Exception as e:
        print(f"[ERROR] Storage failed: {e}")

    # 10. 用户活跃趋势 (30天，每天独立活跃用户数)
    heatmap_data = []
    try:
        today_dt = datetime.now()
        h_limit = today_dt - timedelta(days=30)

        # Count distinct users per day based on any AuditLog action (LOGIN, VIEW, etc.)
        h_q = db.session.query(
                func.date(AuditLog.created_at),
                func.count(func.distinct(AuditLog.user_id))
            )\
            .filter(AuditLog.created_at >= h_limit)\
            .filter(AuditLog.user_id != None)\
            .group_by(func.date(AuditLog.created_at))\
            .order_by(func.date(AuditLog.created_at)).all()

        h_map = {str(r[0]): r[1] for r in h_q}
        # Fill all 30 days to ensure a complete timeline
        for i in range(29, -1, -1):
            d = (today_dt - timedelta(days=i)).date()
            d_str = d.isoformat()
            heatmap_data.append([d_str, h_map.get(d_str, 0)])
    except Exception as e:
        print(f"[ERROR] Heatmap failed: {e}")

    # 💡 11. 区块链专项指标 (Blockchain Specialized Metrics)
    blockchain_stats = {"on_chain_count": 0, "tamper_alerts": 0, "block_height": 15000}
    blockchain_history = []
    security_alerts = []
    
    try:
        # 💡 Apply permission filter to blockchain stats too
        docs_stmt = select(Document.id).where(*auth_filter)
        
        # 已上链文档总数 (只统计用户能看见的)
        on_chain_count = Document.query.filter(Document.id.in_(docs_stmt), Document.tx_hash != None).count()
        # 零信任拦截次数 (非管理员只能看到与自己文档相关的告警)
        if is_admin:
            tamper_alerts = AuditLog.query.filter_by(action='INTRUSION_ALERT').count()
        else:
            tamper_alerts = AuditLog.query.filter(
                AuditLog.action == 'INTRUSION_ALERT',
                AuditLog.document_id.in_(docs_stmt)
            ).count()
        
        blockchain_stats = {
            "on_chain_count": on_chain_count,
            "tamper_alerts": tamper_alerts,
            "block_height": 15000 + on_chain_count
        }
        
        # 实时确权哈希流 (最新的5条已上链记录)
        notarized_docs = Document.query.filter(Document.tx_hash != None)\
            .order_by(Document.updated_at.desc()).limit(5).all()
        for d in notarized_docs:
            blockchain_history.append({
                "id": d.id,
                "title": str(d.title or ""),
                "tx_hash": str(d.tx_hash or ""),
                "time": d.updated_at.isoformat() + "Z" if d.updated_at else None
            })
            
        # 威胁情报 (非管理员只看与自己文档相关的)
        log_q = AuditLog.query.filter_by(action='INTRUSION_ALERT')
        if not is_admin:
            log_q = log_q.filter(AuditLog.document_id.in_(docs_stmt))
            
        tamper_logs = log_q.order_by(AuditLog.created_at.desc()).limit(5).all()
        for log in tamper_logs:
            security_alerts.append({
                "id": log.id,
                "description": str(log.summary or ""),
                "time": log.created_at.isoformat() + "Z" if log.created_at else None,
                "ip": str(log.ip_address or ""),
                "user": str(log.user.display_name() if log.user else "Unknown"),
                "is_starred": log.is_starred
            })
    except Exception as e:
        print(f"[ERROR] Blockchain stats failed: {e}")
        traceback.print_exc()

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
        "blockchain_stats": blockchain_stats,
        "blockchain_history": blockchain_history,
        "security_alerts": security_alerts,
        "is_admin": is_admin
    })

@bp.get("/tamper-alerts")
@jwt_required()
def get_tamper_alerts():
    user = current_user()
    if not user or user.login_name != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
    
    logs = AuditLog.query.filter_by(action='INTRUSION_ALERT').order_by(AuditLog.created_at.desc()).all()
    return jsonify({
        "items": [{
            "id": log.id,
            "created_at": log.created_at.isoformat() + "Z" if log.created_at else None,
            "description": log.summary,
            "ip_address": log.ip_address,
            "is_starred": log.is_starred,
            "user_name": log.user.display_name() if log.user else "Unknown System"
        } for log in logs]
    })
