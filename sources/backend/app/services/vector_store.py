import os
import re
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Determine storage path
storage_root = os.environ.get("STORAGE_PATH")
if storage_root:
    # If in Docker/Prod, use the persistent storage path
    qdrant_path = os.path.join(storage_root, "qdrant_data")
else:
    # Local development fallback
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    qdrant_path = os.path.join(base_dir, "qdrant_data")

# Initialize Qdrant Client (Local Mode)
# It will automatically use fastembed if we call add() or we can manage embeddings manually.
# Using QdrantClient with built-in fastembed support makes it extremely easy.
try:
    client = QdrantClient(path=qdrant_path)
    # Set default model for FastEmbed
    client.set_model("BAAI/bge-small-zh-v1.5")
    COLLECTION_NAME = "edms_documents"
except Exception as e:
    print(f"[VectorStore] Failed to initialize Qdrant Client: {e}")
    client = None

def init_collection():
    if not client:
        return
    try:
        # Check if collection exists
        if not client.collection_exists(COLLECTION_NAME):
            # fastembed automatically configure vectors if we use client.create_collection with fastembed
            # But qdrant_client.create_collection can be called directly or just let add() do it
            pass
    except Exception as e:
        print(f"[VectorStore] Init collection error: {e}")

# Call init
init_collection()

def chunk_text(text: str, max_chunk_size: int = 500) -> List[str]:
    """Simple text chunker by paragraphs and sentences."""
    if not text:
        return []
    
    # Split by double newline (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) <= max_chunk_size:
            current_chunk += "\n" + para if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If a single paragraph is too large, just append it (or further split by sentences)
            current_chunk = para
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def upsert_document(doc_id: int, title: str, text_content: str):
    """
    Chunk the document text and insert/update in Qdrant.
    """
    if not client:
        return
    
    print(f"[VectorStore] Upserting document {doc_id} to vector DB...")
    try:
        chunks = chunk_text(text_content)
        if not chunks:
            # Delete if empty
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="doc_id",
                            match=models.MatchValue(value=doc_id),
                        )
                    ]
                )
            )
            return

        docs = chunks
        metadata = [{"doc_id": doc_id, "title": title, "chunk_index": i} for i in range(len(chunks))]
        # Using fastembed's add method which handles embedding automatically
        # Note: Qdrant client replaces existing points if IDs match. We generate deterministic IDs or just use add()
        
        # First, delete old chunks for this doc_id
        from qdrant_client import models
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchValue(value=doc_id),
                    )
                ]
            )
        )
        
        # Add new chunks
        client.add(
            collection_name=COLLECTION_NAME,
            documents=docs,
            metadata=metadata
        )
        print(f"[VectorStore] Successfully upserted {len(chunks)} chunks for doc {doc_id}")
    except Exception as e:
        print(f"[VectorStore] Error upserting document {doc_id}: {e}")

def search_documents(query: str, doc_ids: List[int], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search across specific documents using vector search.
    """
    if not client:
        return []
        
    try:
        from qdrant_client import models
        
        filter_cond = None
        if doc_ids:
            filter_cond = models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchAny(any=doc_ids),
                    )
                ]
            )
            
        results = client.query(
            collection_name=COLLECTION_NAME,
            query_text=query,
            query_filter=filter_cond,
            limit=limit
        )
        
        # Format results
        contexts = []
        for res in results:
            contexts.append({
                "doc_id": res.metadata.get("doc_id"),
                "title": res.metadata.get("title"),
                "text": res.document,
                "score": res.score
            })
            
        return contexts
    except Exception as e:
        print(f"[VectorStore] Search error: {e}")
        return []
