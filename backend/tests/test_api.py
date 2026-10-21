import io
import uuid
import pytest
from fastapi.testclient import TestClient


def random_email(prefix="student"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@university.edu"


class TestPhase2Backend:
    # 1. Health endpoint
    def test_01_health_endpoint(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AI Study Assistant Backend"

    # 2. User registration
    def test_02_user_registration(self, client: TestClient):
        email = random_email("register")
        payload = {
            "email": email,
            "password": "strongPassword123!",
            "full_name": "Jordan Smith",
            "college": "School of Engineering",
            "major": "Computer Science",
        }
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == email.lower()
        assert "hashed_password" not in data["user"]
        assert "password" not in data["user"]

    # 3. Duplicate registration
    def test_03_duplicate_registration(self, client: TestClient):
        email = random_email("duplicate")
        payload = {
            "email": email,
            "password": "initialPassword123!",
            "full_name": "Alex Taylor",
        }
        # First registration succeeds
        res1 = client.post("/api/auth/register", json=payload)
        assert res1.status_code == 201

        # Second registration with same email fails
        res2 = client.post("/api/auth/register", json=payload)
        assert res2.status_code == 400
        assert "already exists" in res2.json()["detail"].lower()

    # 4. Login success
    def test_04_login_success(self, client: TestClient):
        email = random_email("login_success")
        password = "correctPassword123!"
        # Register user first
        client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": "Login User"},
        )

        # Attempt login
        login_res = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        assert data["user"]["email"] == email.lower()

    # 5. Login failure
    def test_05_login_failure(self, client: TestClient):
        email = random_email("login_fail")
        password = "realPassword123!"
        client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": "Fail Test"},
        )

        # Login with wrong password
        login_res = client.post(
            "/api/auth/login",
            json={"email": email, "password": "WrongPassword999!"},
        )
        assert login_res.status_code == 401
        assert "invalid" in login_res.json()["detail"].lower()

    # 6. GET /auth/me
    def test_06_get_auth_me(self, client: TestClient):
        email = random_email("me_test")
        password = "mySecretPassword123!"
        reg = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": "Self Tester"},
        )
        token = reg.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        me_res = client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        user_info = me_res.json()
        assert user_info["email"] == email.lower()
        assert "hashed_password" not in user_info

    # 7. Invalid JWT
    def test_07_invalid_jwt(self, client: TestClient):
        headers = {"Authorization": "Bearer invalid_malformed_token_12345"}
        res1 = client.get("/api/auth/me", headers=headers)
        assert res1.status_code == 401

        res2 = client.get("/api/documents", headers=headers)
        assert res2.status_code == 401

    # 8. Document creation
    def test_08_document_creation(self, client: TestClient):
        email = random_email("doc_creator")
        password = "testDocPassword123!"
        reg = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": "Doc Creator"},
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create dummy PDF payload
        pdf_content = b"%PDF-1.4 Mock PDF file content for test upload"
        files = {"file": ("calculus_notes.pdf", io.BytesIO(pdf_content), "application/pdf")}

        upload_res = client.post("/api/documents/upload", headers=headers, files=files)
        assert upload_res.status_code == 201
        data = upload_res.json()
        assert data["filename"] == "calculus_notes.pdf"
        assert data["status"] in ["Processing", "Ready"]
        assert "id" in data

    # 9. Document ownership
    def test_09_document_ownership(self, client: TestClient):
        email = random_email("doc_owner")
        password = "ownerPassword123!"
        reg = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": "Doc Owner"},
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Upload a document
        files = {"file": ("linear_algebra.pdf", io.BytesIO(b"%PDF-1.4 sample"), "application/pdf")}
        upload_res = client.post("/api/documents/upload", headers=headers, files=files)
        doc_id = upload_res.json()["id"]

        # Fetch documents
        get_res = client.get("/api/documents", headers=headers)
        assert get_res.status_code == 200
        docs = get_res.json()
        assert any(d["id"] == doc_id for d in docs)

    # 10. Cross-user document isolation
    def test_10_cross_user_document_isolation(self, client: TestClient):
        # User A
        email_a = random_email("user_a")
        reg_a = client.post("/api/auth/register", json={"email": email_a, "password": "passwordA123!"})
        token_a = reg_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # User B
        email_b = random_email("user_b")
        reg_b = client.post("/api/auth/register", json={"email": email_b, "password": "passwordB123!"})
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A uploads a document
        files_a = {"file": ("secret_exam_review.pdf", io.BytesIO(b"%PDF-1.4 Secret"), "application/pdf")}
        doc_a = client.post("/api/documents/upload", headers=headers_a, files=files_a).json()
        doc_a_id = doc_a["id"]

        # User B lists documents -> Must NOT see User A's document
        docs_b = client.get("/api/documents", headers=headers_b).json()
        assert not any(d["id"] == doc_a_id for d in docs_b)

        # User B attempts to access User A's document directly -> 404 Not Found
        direct_get = client.get(f"/api/documents/{doc_a_id}", headers=headers_b)
        assert direct_get.status_code == 404

        # User B attempts to delete User A's document -> 404 Not Found
        delete_res = client.delete(f"/api/documents/{doc_a_id}", headers=headers_b)
        assert delete_res.status_code == 404

        # Document must still exist for User A
        verify_a = client.get(f"/api/documents/{doc_a_id}", headers=headers_a)
        assert verify_a.status_code == 200

    # 11. Chat ownership
    def test_11_chat_ownership(self, client: TestClient):
        # User 1
        email_1 = random_email("chat_user1")
        reg_1 = client.post("/api/auth/register", json={"email": email_1, "password": "password1!"})
        headers_1 = {"Authorization": f"Bearer {reg_1.json()['access_token']}"}

        # User 2
        email_2 = random_email("chat_user2")
        reg_2 = client.post("/api/auth/register", json={"email": email_2, "password": "password2!"})
        headers_2 = {"Authorization": f"Bearer {reg_2.json()['access_token']}"}

        # User 1 sends message
        send_res = client.post(
            "/api/chat",
            headers=headers_1,
            json={"query": "Explain eigenvalues and eigenvectors."},
        )
        assert send_res.status_code == 200
        chat_data = send_res.json()
        assert len(chat_data["answer"]) > 0

        # User 1 checks history -> contains the message
        history_1 = client.get("/api/chat/history", headers=headers_1).json()
        assert len(history_1) >= 2  # user message + assistant placeholder
        assert any(m["text"] == "Explain eigenvalues and eigenvectors." for m in history_1)

        # User 2 checks history -> must be empty (isolated)
        history_2 = client.get("/api/chat/history", headers=headers_2).json()
        assert len(history_2) == 0

    # 12. Progress ownership
    def test_12_progress_ownership(self, client: TestClient):
        # New user receives authentic zero-state
        email_new = random_email("zero_progress")
        reg_new = client.post("/api/auth/register", json={"email": email_new, "password": "passwordZero1!"})
        headers_new = {"Authorization": f"Bearer {reg_new.json()['access_token']}"}

        summary_res = client.get("/api/progress/summary", headers=headers_new)
        assert summary_res.status_code == 200
        summary = summary_res.json()
        assert summary["total_questions_answered"] == 0
        assert summary["correct_answers"] == 0
        assert summary["average_mastery"] == 0.0
        assert summary["topics"] == []

    # 13. Database constraints & Foreign Keys
    def test_13_foreign_key_and_cascades(self, client: TestClient, db_session):
        from app.db.models import User, Document, Chat, Message
        email = random_email("cascade_user")
        reg = client.post("/api/auth/register", json={"email": email, "password": "password123!"})
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Upload document and chat message
        client.post("/api/documents/upload", headers=headers, files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")})
        client.post("/api/chat", headers=headers, json={"query": "Testing cascade deletion."})

        user = db_session.query(User).filter(User.email == email).first()
        user_id = user.id
        assert db_session.query(Document).filter(Document.user_id == user_id).count() == 1
        assert db_session.query(Chat).filter(Chat.user_id == user_id).count() == 1

        # Delete user -> Foreign key cascade deletes documents, chats, messages
        db_session.delete(user)
        db_session.commit()

        assert db_session.query(Document).filter(Document.user_id == user_id).count() == 0
        assert db_session.query(Chat).filter(Chat.user_id == user_id).count() == 0
