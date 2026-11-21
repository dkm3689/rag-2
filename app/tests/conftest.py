import os

os.environ["DATABASE_URL"] = "postgresql+psycopg://rag:rag@localhost:5432/rag_test"

import pytest

from fastapi.testclient import TestClient


from app.database import Base, engine

from app.main import app

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_headers(client):
    def _make(email: str) -> dict :
        client.post("/auth/signup", json={ "email":email, "password":"password123" } )
        response = client.post(
            "/auth/login", data = { "username": email, "password":"password123" }
        )
        print("Login response for", email, ":", response.json())
        token = response.json()["access_token"]
        print("Token for", email, ":", token)
        return { "Authorization": f"Bearer {token}" }
        

    return _make