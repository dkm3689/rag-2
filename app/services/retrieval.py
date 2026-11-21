from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services.embeddings import embed_texts

from app.models import Chunk, Document

def search_chunks( db:Session, question:str , user_id:int,  top_k:int=4, document_id:int | None = None ):
    query_vector = embed_texts([question])[0]

    distance = Chunk.embedding.cosine_distance(query_vector)

    stmt = (
        select(Chunk, distance.label("distance") )
        .join(Document, Chunk.document_id==Document.id )
        .where(Document.owner_id == user_id)
        .order_by(distance)
        .limit(top_k)
    )

    if document_id is not None:
        stmt = stmt.where(Chunk.document_id == document_id)
    
    return db.execute(stmt).all()