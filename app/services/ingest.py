from app.database import SessionLocal
from app.services.chunking import chunk_text
from app.services.embeddings import embed_texts
from app.models import Chunk, Document


def ingest_text(doc_id:int) -> None:
    db = SessionLocal()
    try:

        doc = db.get(Document, doc_id)
        if doc is None:
            print("doc is not there")
            raise Exception("Doc not found")
        
        pieces = chunk_text(doc.content)
        
        vectors = embed_texts(pieces)

        for piece, vector in zip(pieces, vectors):
            db.add(Chunk(document_id=doc.id, content=piece, embedding=vector  ))
        
        doc.status="ready"
        db.commit()
    
    except Exception:
        db.rollback()
        doc = db.get(Document, doc_id )
        if doc is not None:
            doc.status = "failed"
            db.commit()
        return
    
    finally:
        db.close()