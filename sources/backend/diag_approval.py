from app import create_app
from app.extensions import db
from app.models.document import Document
from app.services.approval_service import start_flow
import sys

app = create_app()
with app.app_context():
    doc_id = 60 # 刚才转圈的那个文档
    doc = db.session.get(Document, doc_id)
    if not doc:
        print(f"Doc {doc_id} not found")
        sys.exit(1)
    
    print(f"Attempting to start flow for doc {doc_id}...")
    try:
        # 尝试模拟正常审批流程
        flow = start_flow(doc, "parallel", [1]) # 1 通常是 admin
        db.session.commit()
        print(f"SUCCESS: Flow created with ID {flow.id}")
    except Exception as e:
        db.session.rollback()
        print(f"FAILED: {str(e)}")
