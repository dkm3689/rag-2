from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine, Base
from app.routers import documents, auth, ask


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    yield



app = FastAPI(title="RAG API", lifespan=lifespan)


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(ask.ask_router)