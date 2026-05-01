"""Global audit logging decorator for API endpoints."""
from functools import wraps
from flask import request
from app.extensions import db
from app.models.workflow import AuditLog
from app.utils.auth import current_user


def audit_log_required(action: str):
    """
    Decorator to automatically log user actions on documents.
    Captures: user_id, document_id (from URL), ip_address, action.
    Logs are inserted AFTER the response is sent (non-blocking).
    
    Usage:
        @audit_log_required("VIEW")
        def get_document(doc_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Execute the original function first
            response = f(*args, **kwargs)

            # Only log on successful responses (2xx)
            try:
                status_code = response[1] if isinstance(response, tuple) else 200
                if isinstance(response, tuple):
                    status_code = response[1]
                elif hasattr(response, 'status_code'):
                    status_code = response.status_code
                else:
                    status_code = 200

                if 200 <= status_code < 300:
                    user = current_user()
                    doc_id = kwargs.get("doc_id") or kwargs.get("document_id") or kwargs.get("id")

                    # Try to extract from URL rule if not in kwargs
                    if doc_id is None and request.view_args:
                        doc_id = request.view_args.get("doc_id") or request.view_args.get("id")

                    log = AuditLog(
                        user_id=user.id if user else None,
                        document_id=int(doc_id) if doc_id else None,
                        action=action,
                        summary=f"{action}: {request.method} {request.path}",
                        ip_address=request.remote_addr,
                        # 💡 NEW: Intrusion alerts are auto-starred
                        is_starred=(action == "INTRUSION_ALERT")
                    )
                    db.session.add(log)
                    
                    # 💡 Proactive Cleanup: 
                    from datetime import datetime, timedelta
                    now = datetime.utcnow()
                    cutoff_24h = now - timedelta(hours=24)
                    cutoff_2d = now - timedelta(days=2)
                    
                    # Delete logic:
                    # 1. Normal unstarred logs older than 24h
                    # 2. INTRUSION_ALERT unstarred logs older than 2 days (based on unstarred_at)
                    
                    # Delete normal unstarred logs
                    AuditLog.query.filter(
                        AuditLog.is_starred == False,
                        AuditLog.action != "INTRUSION_ALERT",
                        AuditLog.created_at < cutoff_24h
                    ).delete()
                    
                    # Delete unstarred intrusion alerts after 2 days
                    AuditLog.query.filter(
                        AuditLog.is_starred == False,
                        AuditLog.action == "INTRUSION_ALERT",
                        AuditLog.unstarred_at != None,
                        AuditLog.unstarred_at < cutoff_2d
                    ).delete()
                    
                    db.session.commit()
            except Exception:
                # Audit logging should never break the main request
                pass

            return response
        return wrapper
    return decorator
