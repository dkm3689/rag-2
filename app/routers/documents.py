from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, User
from app.schemas import DocumentCreate, DocumentOut, ChunkOut
from app.services.ingest import ingest_text

from app.dependencies import get_current_user

from fastapi import File, UploadFile, BackgroundTasks
from pypdf import PdfReader

from app.services.retrieval import search_chunks

router = APIRouter(prefix="/documents", tags=["documents"])


print("Inside documents router")

def get_owned_document(doc_id: int, user: User, db: Session) -> Document:
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.owner_id == user.id)
        .first()
    )
    print("inside get_owned_document - Found document:", doc)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

print("Inside documents router - after get_owned_document definition")

@router.get('', response_model=list[DocumentOut])
def get_documents(db:Session=Depends(get_db), user: User = Depends(get_current_user)):
    print("Getting documents for user:", user.id)
    return db.query(Document).filter( Document.owner_id == user.id ).all()


@router.get("/search")
def search(q:str, db=Depends(get_db), user: User = Depends(get_current_user)):
    results = search_chunks(db, q, user_id=user.id)

    return [
        {
            "id":chunk.id,
            "document_id": chunk.document_id,
            "content": chunk.content,
            "score": round(1-distance,3)
        }
        for chunk, distance in results 
    ]


@router.post('', status_code=201, response_model=DocumentOut)
def create_document(doc:DocumentCreate, db:Session=Depends(get_db), user: User = Depends(get_current_user) ):
    new_doc = Document(title=doc.title, content=doc.content, owner_id=user.id )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    ingest_text(new_doc.id)
    return new_doc



# @router.get('/{documentid}',  response_model=DocumentOut)
# def get_owned_document(documentid:int, db:Session=Depends(get_db), user: User = Depends(get_current_user)):
#     doc = db.query(Document).filter(Document.id == documentid).first()
#     if doc is None:
#         raise HTTPException(status_code=404, detail="Document not found")
#     return doc
  
@router.get("/{documentid}", response_model=DocumentOut)
def get_document(
    documentid: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_owned_document(documentid, user, db)



@router.delete('/{doc_id}')
def delete_document(doc_id:int, db:Session=Depends(get_db), user:User = Depends(get_current_user)):
    doc = get_owned_document(doc_id, user, db)
    # doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    print("Document deleted")
    return {"Message": "Document deleted successfully"}
 

@router.get('/{doc_id}/chunks', response_model=list[ChunkOut])
def get_chunks(doc_id: int, db: Session = Depends(get_db), user: User=Depends(get_current_user)):
    # document = db.query(Document).filter(Document.id == doc_id).first()
    doc = get_owned_document(doc_id, user, db)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.chunks


@router.post( "/upload", status_code=201, response_model = DocumentOut )
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
    ):

        print("Uploading document for user:", user.id, "Filename:", file.filename)
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="File must only be PDF")

        reader = PdfReader(file.file)

        text = "\n".join( page.extract_text() or "" for page in reader.pages ).strip()

        if not text:
            raise HTTPException(status_code=400, detail="Its not a PDf" )

        new_doc = Document( title=file.filename, content = text , owner_id = user.id )

        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        background_tasks.add_task(ingest_text, new_doc.id)
        
        return new_doc