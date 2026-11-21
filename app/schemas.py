from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime

class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    status: str

class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str

class AskRequest(BaseModel):
    question: str = Field()
    top_k: int = Field(default=4, ge=1, le=10)
    document_id: int | None = Field(default=None)

class Source(BaseModel):
    chunk_id: int
    document_id: int
    content: str
    rank: float

class AskResponse(BaseModel):
    answer: str
    sources: list[Source]

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str