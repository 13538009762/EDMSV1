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
                    )
                    db.session.add(log)
                    db.session.commit()
            except Exception:
                # Audit logging should never break the main request
                pass

            return response
        return wrapper
    return decorator
