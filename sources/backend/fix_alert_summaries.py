from app import create_app
from app.extensions import db
from app.models.workflow import AuditLog

app = create_app()
with app.app_context():
    # Only fix INTRUSION_ALERT summaries for now as they are the ones causing issues in dashboard
    alerts = AuditLog.query.filter_by(action='INTRUSION_ALERT').all()
    correct_summary = '【零信任拦截】用户发起确权审计，系统比对发现底层物理数据已被未知来源非法篡改，已阻断！'
    
    count = 0
    for a in alerts:
        # Check if it looks mangled (contains replacement characters or non-ascii/non-chinese garbage)
        # Or just overwrite all INTRUSION_ALERT summaries since we know what they should be
        a.summary = correct_summary
        count += 1
    
    db.session.commit()
    print(f"Fixed {count} alert summaries.")
