from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models import Document, User
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint("dashboard", __name__)

@bp.get("/stats")
@jwt_required()
def get_stats():
    # 1. Total counts
    total_users = db.session.query(User).count()
    total_docs = db.session.query(Document).count()
    
    # 2. Document Status Breakdown
    status_counts = db.session.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
    status_data = [{"status": row[0], "count": row[1]} for row in status_counts]

    # Fill in valid statuses if missing
    found_statuses = {row[0] for row in status_counts}
    for s in ["draft", "in_approval", "approved", "rejected"]:
        if s not in found_statuses:
            status_data.append({"status": s, "count": 0})

    # 3. Documents updated over the last 7 days trend
    trend_data = []
    today = datetime.utcnow().date()
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        # We query the docs where updated_at falls on target_date
        count = db.session.query(Document).filter(
            func.date(Document.updated_at) == target_date
        ).count()
        trend_data.append({
            "date": target_date.strftime("%Y-%m-%d"),
            "count": count
        })

    return jsonify({
        "total_users": total_users,
        "total_docs": total_docs,
        "status_data": status_data,
        "trend_data": trend_data
    })
