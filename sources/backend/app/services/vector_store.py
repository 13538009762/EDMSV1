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
        exists = client.collection_exists(COLLECTION_NAME)
        if exists:
            try:
                info = client.get_collection(COLLECTION_NAME)
                vectors = info.config.params.vectors
                # If vectors is not a dict, or our specific fastembed key is not in it:
                if not isinstance(vectors, dict) or "fast-bge-small-zh-v1.5" not in vectors:
                    print(f"[VectorStore] Incompatible collection '{COLLECTION_NAME}' detected. Recreating...")
                    client.delete_collection(COLLECTION_NAME)
                    exists = False
            except Exception as e:
                print(f"[VectorStore] Error checking collection schema: {e}. Recreating...")
                try:
                    client.delete_collection(COLLECTION_NAME)
                except Exception:
                    pass
                exists = False

        if not exists:
            # Create collection with default vector params matching fastembed requirements
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=client.get_fastembed_vector_params()
            )
            print(f"[VectorStore] Created collection '{COLLECTION_NAME}' with correct fastembed vector params.")
            
        # 💡 Add Full-Text Index for BM25-like keyword search
        from qdrant_client import models
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="document",
            field_schema=models.TextIndexParams(
                type="text",
                tokenizer=models.TokenizerType.MULTILINGUAL,
                min_token_len=2,
                lowercase=True,
            )
        )
        # Also index doc_id for fast filtering
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="doc_id",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
    except Exception as e:
        print(f"[VectorStore] Init collection error: {e}")

# Call init
init_collection()

def chunk_text(text: str, max_chunk_size: int = 800) -> List[str]:
    """
    Advanced Markdown-aware chunker.
    Splits by headings (H1-H6) first, then by paragraphs.
    Maintains semantic independence by including the heading in each chunk.
    """
    if not text:
        return []

    # 1. Split by Markdown headings (lines starting with #)
    # We use a regex that captures the heading and the following text
    parts = re.split(r'(^#{1,6}\s+.*$)', text, flags=re.MULTILINE)
    
    sections = []
    current_heading = "正文"
    
    # re.split with capturing groups returns the matches as well
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        if part.startswith('#'):
            current_heading = part
        else:
            sections.append({
                "heading": current_heading,
                "content": part
            })
            
    # Handle case where there are no headings
    if not sections and text:
        sections.append({"heading": "", "content": text})

    final_chunks = []
    for sec in sections:
        heading = sec["heading"]
        content = sec["content"]
        
        # Split section content into paragraphs
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_chunk = heading + "\n" if heading else ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # If adding this paragraph exceeds limit, push current chunk and start new
            if len(current_chunk) + len(para) > max_chunk_size:
                if current_chunk.strip() and current_chunk != (heading + "\n"):
                    final_chunks.append(current_chunk.strip())
                
                # Start new chunk with heading for context
                current_chunk = (heading + "\n" if heading else "") + para
            else:
                current_chunk += "\n\n" + para if current_chunk and current_chunk != (heading + "\n") else para
        
        if current_chunk.strip():
            final_chunks.append(current_chunk.strip())
            
    return final_chunks

def recreate_incompatible_collection(e: Exception):
    print(f"[VectorStore] Incompatible or missing collection detected: {e}. Recreating...")
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception as delete_err:
        print(f"[VectorStore] Failed to delete collection during recovery: {delete_err}")
        
    try:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=client.get_fastembed_vector_params()
        )
        from qdrant_client import models
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="document",
            field_schema=models.TextIndexParams(
                type="text",
                tokenizer=models.TokenizerType.MULTILINGUAL,
                min_token_len=2,
                lowercase=True,
            )
        )
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="doc_id",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        print(f"[VectorStore] Recreated collection '{COLLECTION_NAME}' successfully.")
    except Exception as create_err:
        print(f"[VectorStore] Error during collection recovery: {create_err}")

def upsert_document(doc_id: int, title: str, text_content: str):
    """
    Chunk the document text and insert/update in Qdrant.
    """
    if not client:
        return
    
    print(f"[VectorStore] Upserting document {doc_id} to vector DB...")
    
    def _execute_upsert():
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

    try:
        _execute_upsert()
    except Exception as e:
        error_msg = str(e)
        if "incompatible vector params" in error_msg.lower() or "not found" in error_msg.lower():
            recreate_incompatible_collection(e)
            try:
                print(f"[VectorStore] Retrying upsert for document {doc_id}...")
                _execute_upsert()
            except Exception as retry_err:
                print(f"[VectorStore] Error during collection recovery and retry: {retry_err}")
        else:
            print(f"[VectorStore] Error upserting document {doc_id}: {e}")

def search_documents(query: str, doc_ids: List[int], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search across specific documents using vector search.
    """
    if not client:
        return []
        
    def _execute_search():
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

    try:
        return _execute_search()
    except Exception as e:
        error_msg = str(e)
        if "incompatible vector params" in error_msg.lower() or "not found" in error_msg.lower():
            recreate_incompatible_collection(e)
            try:
                print("[VectorStore] Retrying search...")
                return _execute_search()
            except Exception as retry_err:
                print(f"[VectorStore] Recovery during search failed: {retry_err}")
                return []
        else:
            print(f"[VectorStore] Search error: {e}")
            return []
