"""AI对话历史内存存储服务"""
from datetime import datetime
from typing import List, Dict, Optional
import threading


class AIHistoryStore:
    """线程安全的AI对话历史内存存储"""
    
    def __init__(self):
        self._store: List[Dict] = []
        self._lock = threading.Lock()
        self._next_id = 1
    
    def add_conversation(self, user_id: int, user_name: str, question: str, 
                        answer: str, document_id: Optional[int] = None,
                        document_title: Optional[str] = None,
                        context_url: Optional[str] = None,
                        action_type: str = "chat",
                        tokens_used: Optional[int] = None) -> Dict:
        """添加对话记录"""
        with self._lock:
            conversation = {
                "id": self._next_id,
                "user_id": user_id,
                "user_name": user_name,
                "document_id": document_id,
                "document_title": document_title,
                "question": question,
                "answer": answer,
                "context_url": context_url,
                "action_type": action_type,
                "created_at": datetime.utcnow().isoformat(),
                "tokens_used": tokens_used,
            }
            self._store.append(conversation)
            self._next_id += 1
            
            # 控制台打印详细信息
            print("\n" + "="*80)
            print(f"[AI HISTORY] New Conversation #{conversation['id']}")
            print("="*80)
            print(f"User: {user_name} (ID: {user_id})")
            print(f"Document: {document_title or 'N/A'} (ID: {document_id or 'N/A'})")
            print(f"Time: {conversation['created_at']}")
            print(f"Type: {action_type}")
            print("-"*80)
            print(f"Question:\n{question[:500]}{'...' if len(question) > 500 else ''}")
            print("-"*80)
            print(f"Answer:\n{answer[:500]}{'...' if len(answer) > 500 else ''}")
            print("="*80 + "\n")
            
            return conversation
    
    def get_all(self, page: int = 1, per_page: int = 20, 
                document_id: Optional[int] = None,
                user_id: Optional[int] = None) -> Dict:
        """获取分页历史记录"""
        with self._lock:
            filtered = self._store.copy()
            
            # 过滤条件
            if document_id:
                filtered = [c for c in filtered if c.get("document_id") == document_id]
            if user_id:
                filtered = [c for c in filtered if c.get("user_id") == user_id]
            
            # 按时间倒序
            filtered.sort(key=lambda x: x["created_at"], reverse=True)
            
            # 分页
            total = len(filtered)
            start = (page - 1) * per_page
            end = start + per_page
            items = filtered[start:end]
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page if per_page > 0 else 0
            }
    
    def delete(self, conv_id: int) -> bool:
        """删除单条记录"""
        with self._lock:
            for i, conv in enumerate(self._store):
                if conv["id"] == conv_id:
                    self._store.pop(i)
                    print(f"[AI HISTORY] Deleted conversation #{conv_id}")
                    return True
            return False
    
    def clear(self, document_id: Optional[int] = None, user_id: Optional[int] = None) -> int:
        """清空历史记录"""
        with self._lock:
            if document_id:
                original_count = len(self._store)
                self._store = [c for c in self._store if c.get("document_id") != document_id]
                deleted = original_count - len(self._store)
            elif user_id:
                original_count = len(self._store)
                self._store = [c for c in self._store if c.get("user_id") != user_id]
                deleted = original_count - len(self._store)
            else:
                deleted = len(self._store)
                self._store.clear()
            
            print(f"[AI HISTORY] Cleared {deleted} conversations")
            return deleted
    
    def get_count(self) -> int:
        """获取总记录数"""
        with self._lock:
            return len(self._store)


# 全局单例
ai_history_store = AIHistoryStore()
