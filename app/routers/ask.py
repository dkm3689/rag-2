from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import AskRequest, AskResponse, Source

from app.services.retrieval import search_chunks

from app.services.llm import answer_question

from app.database import get_db

from app.dependencies import get_current_user

ask_router = APIRouter()

#  db:Session, question:str  , top_k:int=4, document_id:int | None = None


@ask_router.post("/ask", response_model=AskResponse)
def ask_question( body: AskRequest, db: Session=Depends(get_db), user = Depends(get_current_user) ):
    print("inside ask_question")
    results = search_chunks( db, body.question, user.id, body.top_k, body.document_id )

    if results is None:
        raise HTTPException(status_code=404, detail="Not found")
    
    chunk_texts = [ chunk.content for chunk, _ in results ]

    answer = answer_question( body.question, chunk_texts  )
 
    sources = [
          Source(
            chunk_id = chunk.id,
            document_id = chunk.document_id,
            content = chunk.content,
            rank = round( 1 - distance , 3)
          )

        for chunk, distance in results
    ]

    return AskResponse(answer=answer, sources=sources)