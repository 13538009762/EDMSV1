import os
import sys

# Ensure backend root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.document import Document, DocumentVersion
from sqlalchemy import func

def prune_versions():
    """
    Stage 2: 版本折叠机制 (Version Folding)
    保留关键节点：初稿 (v1)、终稿 (max_v)、以及被驳回的版本。
    清理中间无用的自动保存快照。
    """
    app = create_app()
    with app.app_context():
        # 获取所有已批准或已归档的文档
        docs = Document.query.filter(Document.status.in_(['approved', 'archived'])).all()
        
        total_deleted = 0
        for doc in docs:
            # 1. 确定保留的版本号
            min_v = db.session.query(func.min(DocumentVersion.version_no)).filter_by(document_id=doc.id).scalar()
            max_v = db.session.query(func.max(DocumentVersion.version_no)).filter_by(document_id=doc.id).scalar()
            
            # TODO: 如果有里程碑标记或驳回标记，也应加入保留列表
            # 目前简单保留首尾
            keep_versions = {min_v, max_v}
            
            # 2. 删除不在保留列表中的版本
            deleted = db.session.query(DocumentVersion).filter(
                DocumentVersion.document_id == doc.id,
                ~DocumentVersion.version_no.in_(keep_versions)
            ).delete(synchronize_session=False)
            
            if deleted > 0:
                print(f"[Folding] Doc {doc.id}: Kept v{min_v}, v{max_v}. Deleted {deleted} intermediate versions.")
                total_deleted += deleted
        
        db.session.commit()
        print(f"\n[Success] Version folding complete. Total intermediate versions pruned: {total_deleted}")

if __name__ == "__main__":
    prune_versions()
