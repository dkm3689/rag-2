from app.tests.conftest import client, auth_headers

def test_signup_and_duplicate(client):
    body = { "email":"dup@test.com", "password": "password123" }
    assert client.post("/auth/signup", json=body).status_code == 201
    assert client.post("/auth/signup", json=body).status_code == 409

def test_wrong_password(client):
    client.post("/auth/signup", json={ "email": "wp@test.com", "password": "password123" } )
    response = client.post( "/auth/login",  data={ "username":"wp@test.com", "password":"wrong_pass" } )
    assert response.status_code == 401

def test_documents_require_login(client):
    assert client.get("/documents").status_code == 401


def test_users_cannot_see_each_others_documents(client, auth_headers):
    alice = auth_headers("alice@test.com")
    bob = auth_headers("bob@test.com")

    created = client.post(
        "/documents",
        json = { "title":"Secret", "content": "alice's private notes." },
        headers = alice
    )
    doc_id = created.json()["id"]

    assert client.get("/documents", headers = bob).json() == []
    assert client.get(f"/documents/{doc_id}", headers=bob).status_code == 404
    assert client.get(f"/documents/{doc_id}", headers=alice).status_code == 200