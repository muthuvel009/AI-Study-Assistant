import io
import uuid
import pytest
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db.models import Document, DocumentChunk, Quiz, Question, Progress, Recommendation
from app.services.pdf_service import extract_pdf_pages
from app.services.chunking_service import chunk_extracted_pages
from app.services.processing_service import process_document_background
from app.services.quiz_service import parse_and_validate_quiz_json, grade_quiz_submission
from app.services.recommendation_service import generate_recommendations_for_user
from tests.test_phase3 import generate_valid_pdf_bytes, random_email


class TestPhase4LearningAndQuizzes:

    # Helper to register user and upload a study document
    @classmethod
    def setup_user_with_document(cls, client: TestClient, prefix="student_p4"):
        email = random_email(prefix)
        reg = client.post(
            "/api/auth/register",
            json={"email": email, "password": "StrongPassword123!", "full_name": "Test Learner"},
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create sample notes on Networking & Operating Systems
        content = [
            "Computer Networking: The Transmission Control Protocol (TCP) provides reliable, ordered, and error-checked delivery of a stream of octets between applications running on hosts communicating via an IP network. Major features include three-way handshake, flow control via sliding window, and congestion avoidance algorithms.",
            "Domain Name System (DNS) is a hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet or a private network. It translates more readily memorized domain names to the numerical IP addresses needed for locating and identifying computer services.",
        ]
        pdf_bytes = generate_valid_pdf_bytes(content)
        files = {"file": ("networking_notes.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        upload_res = client.post("/api/documents/upload", headers=headers, files=files)
        doc_id = upload_res.json()["id"]

        # Run background processing synchronously
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            process_document_background(doc.id, doc.file_path)
        finally:
            db.close()

        return headers, doc_id, email

    # 1. Quiz generation via semantic RAG
    def test_01_quiz_generation_semantic_rag(self, client: TestClient):
        headers, doc_id, _ = self.setup_user_with_document(client, "quiz_gen")
        payload = {
            "document_id": doc_id,
            "topic": "Transmission Control Protocol",
            "difficulty": "Medium",
            "num_questions": 3,
        }
        res = client.post("/api/quizzes/generate", headers=headers, json=payload)
        assert res.status_code == 201
        data = res.json()
        assert "id" in data
        assert data["topic"] == "Transmission Control Protocol"
        assert data["difficulty"] == "Medium"
        assert len(data["questions"]) == 3

    # 2. Topic-aware retrieval
    def test_02_topic_aware_retrieval(self, client: TestClient):
        headers, doc_id, _ = self.setup_user_with_document(client, "topic_retrieval")
        # Generate on DNS
        res = client.post(
            "/api/quizzes/generate",
            headers=headers,
            json={"document_id": doc_id, "topic": "Domain Name System", "difficulty": "Hard", "num_questions": 2},
        )
        assert res.status_code == 201
        data = res.json()
        assert len(data["questions"]) == 2
        # Questions should relate to DNS
        assert any("dns" in q["question_text"].lower() or "domain" in q["question_text"].lower() for q in data["questions"])

    # 3. Quiz JSON validation (valid)
    def test_03_quiz_json_validation(self):
        valid_json = """[
            {
                "question": "What is the primary role of the Transmission Control Protocol?",
                "options": [
                    "Reliable, ordered, error-checked stream delivery",
                    "Unreliable connectionless datagram delivery",
                    "Hardware MAC address resolution only",
                    "Physical optical cable transmission"
                ],
                "correct_answer": "Reliable, ordered, error-checked stream delivery",
                "explanation": "TCP ensures reliable and ordered transmission using sequence numbers and acknowledgements.",
                "topic": "Networking"
            }
        ]"""
        validated = parse_and_validate_quiz_json(valid_json, expected_count=1, default_topic="Networking")
        assert len(validated) == 1
        assert validated[0]["question_text"] == "What is the primary role of the Transmission Control Protocol?"
        assert len(validated[0]["options"]) == 4
        assert validated[0]["correct_answer"] == "Reliable, ordered, error-checked stream delivery"

    # 4. Invalid Gemini output handling
    def test_04_invalid_gemini_output_handling(self):
        invalid_raw = "This is just conversational text without any JSON array."
        with pytest.raises(ValueError) as exc:
            parse_and_validate_quiz_json(invalid_raw, expected_count=2, default_topic="Networking")
        assert "not valid JSON" in str(exc.value)

    # 5. Wrong question count rejection
    def test_05_wrong_question_count_rejection(self):
        json_two_questions = """[
            {"question": "Q1?", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "E1", "topic": "T"},
            {"question": "Q2?", "options": ["A", "B", "C", "D"], "correct_answer": "B", "explanation": "E2", "topic": "T"}
        ]"""
        with pytest.raises(ValueError) as exc:
            parse_and_validate_quiz_json(json_two_questions, expected_count=5, default_topic="T")
        assert "count mismatch" in str(exc.value).lower()

    # 6. Invalid correct answer rejection (does not match options)
    def test_06_invalid_correct_answer_rejection(self):
        json_mismatched = """[
            {"question": "What is the primary protocol used here?", "options": ["Alpha", "Beta", "Gamma", "Delta"], "correct_answer": "Omega", "explanation": "E1", "topic": "T"}
        ]"""
        with pytest.raises(ValueError) as exc:
            parse_and_validate_quiz_json(json_mismatched, expected_count=1, default_topic="T")
        assert "does not match any of the options" in str(exc.value).lower()

    # 7. Hidden answer payload before submission
    def test_07_hidden_answer_payload(self, client: TestClient):
        headers, doc_id, _ = self.setup_user_with_document(client, "hidden_answers")
        gen_res = client.post(
            "/api/quizzes/generate",
            headers=headers,
            json={"document_id": doc_id, "topic": "TCP Flow Control", "difficulty": "Easy", "num_questions": 2},
        )
        assert gen_res.status_code == 201
        quiz = gen_res.json()
        quiz_id = quiz["id"]

        # 1. Verification on generation payload
        for q in quiz["questions"]:
            assert "correct_answer" not in q
            assert "explanation" not in q
            assert "options" in q
            assert len(q["options"]) == 4

        # 2. Verification on GET /api/quizzes/{id}
        get_res = client.get(f"/api/quizzes/{quiz_id}", headers=headers)
        assert get_res.status_code == 200
        get_quiz = get_res.json()
        for q in get_quiz["questions"]:
            assert "correct_answer" not in q
            assert "explanation" not in q

    # 8. Quiz submission & server scoring
    def test_08_quiz_submission_and_server_scoring(self, client: TestClient):
        headers, doc_id, _ = self.setup_user_with_document(client, "quiz_submit")
        gen_res = client.post(
            "/api/quizzes/generate",
            headers=headers,
            json={"document_id": doc_id, "topic": "Network Protocols", "difficulty": "Medium", "num_questions": 2},
        )
        quiz = gen_res.json()
        quiz_id = quiz["id"]
        q1_id = quiz["questions"][0]["id"]
        q2_id = quiz["questions"][1]["id"]

        # Student picks option A for both
        answers = {
            q1_id: quiz["questions"][0]["options"][0],
            q2_id: quiz["questions"][1]["options"][0],
        }

        sub_res = client.post(f"/api/quizzes/{quiz_id}/submit", headers=headers, json={"answers": answers})
        assert sub_res.status_code == 200
        results = sub_res.json()
        assert "score" in results
        assert "percentage" in results
        assert results["total_questions"] == 2
        assert len(results["question_results"]) == 2

        # Explanations and correctness now revealed
        for qr in results["question_results"]:
            assert "is_correct" in qr
            assert "correct_answer" in qr
            assert qr["explanation"] is not None

    # 9. Server-side scoring authoritative
    def test_09_server_side_scoring_authoritative(self, client: TestClient):
        headers, doc_id, _ = self.setup_user_with_document(client, "auth_score")
        gen_res = client.post(
            "/api/quizzes/generate",
            headers=headers,
            json={"document_id": doc_id, "topic": "DNS Hierarchy", "difficulty": "Medium", "num_questions": 2},
        )
        quiz = gen_res.json()
        quiz_id = quiz["id"]

        # Look up correct answers directly from DB to verify server computes exact 100%
        db = SessionLocal()
        try:
            questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
            answers = {q.id: q.correct_answer for q in questions}
        finally:
            db.close()

        sub_res = client.post(f"/api/quizzes/{quiz_id}/submit", headers=headers, json={"answers": answers})
        assert sub_res.status_code == 200
        data = sub_res.json()
        assert data["score"] == 100.0
        assert data["correct_count"] == 2

    # 10. Empty quiz error handling (400)
    def test_10_empty_quiz_error_handling(self, client: TestClient):
        email = random_email("empty_quiz")
        reg = client.post("/api/auth/register", json={"email": email, "password": "Password123!", "full_name": "EQ"}).json()
        user_id = reg["user"]["id"]
        db = SessionLocal()
        try:
            # Create an empty quiz manually
            empty_quiz = Quiz(user_id=user_id, title="Empty", topic="None", difficulty="Easy")
            db.add(empty_quiz)
            db.commit()
            db.refresh(empty_quiz)

            with pytest.raises(Exception) as exc:
                grade_quiz_submission(empty_quiz.id, user_id, {}, db)
            assert "400" in str(exc.value) or "empty" in str(exc.value).lower()
        finally:
            db.close()

    # 11. Quiz ownership enforcement
    def test_11_quiz_ownership(self, client: TestClient):
        headers_a, doc_id_a, _ = self.setup_user_with_document(client, "owner_a")
        headers_b, _, _ = self.setup_user_with_document(client, "owner_b")

        # User A generates quiz
        q_res = client.post(
            "/api/quizzes/generate",
            headers=headers_a,
            json={"document_id": doc_id_a, "topic": "TCP", "difficulty": "Easy", "num_questions": 2},
        )
        quiz_a_id = q_res.json()["id"]

        # User B attempts to access User A's quiz -> 404
        get_b = client.get(f"/api/quizzes/{quiz_a_id}", headers=headers_b)
        assert get_b.status_code == 404

        # User B attempts to submit User A's quiz -> 404
        sub_b = client.post(f"/api/quizzes/{quiz_a_id}/submit", headers=headers_b, json={"answers": {}})
        assert sub_b.status_code == 404

    # 12. Progress update after quiz
    def test_12_progress_update_after_quiz(self, client: TestClient):
        headers, doc_id, email = self.setup_user_with_document(client, "prog_update")
        # Generate & submit quiz
        gen_res = client.post(
            "/api/quizzes/generate",
            headers=headers,
            json={"document_id": doc_id, "topic": "TCP Handshake", "difficulty": "Medium", "num_questions": 2},
        )
        quiz_id = gen_res.json()["id"]
        client.post(f"/api/quizzes/{quiz_id}/submit", headers=headers, json={"answers": {}})

        # Check progress summary
        prog_res = client.get("/api/progress/summary", headers=headers)
        assert prog_res.status_code == 200
        prog = prog_res.json()
        assert prog["total_questions_answered"] >= 2
        assert len(prog["topics"]) >= 1
        assert any(t["topic"] == "TCP Handshake" for t in prog["topics"])

    # 13. Mastery calculation formula (moving average)
    def test_13_mastery_calculation_moving_average(self, client: TestClient):
        headers, doc_id, _ = self.setup_user_with_document(client, "mastery_formula")
        topic = "Congestion Control"

        # Quiz 1
        q1 = client.post("/api/quizzes/generate", headers=headers, json={"document_id": doc_id, "topic": topic, "num_questions": 2}).json()
        # Submit all correct -> 100%
        db = SessionLocal()
        try:
            questions1 = db.query(Question).filter(Question.quiz_id == q1["id"]).all()
            ans1 = {q.id: q.correct_answer for q in questions1}
        finally:
            db.close()
        client.post(f"/api/quizzes/{q1['id']}/submit", headers=headers, json={"answers": ans1})

        # Check mastery after Attempt 1 = 100%
        topic_prog1 = client.get(f"/api/progress/{topic}", headers=headers).json()
        assert topic_prog1["mastery_score"] == 100.0
        assert topic_prog1["quiz_attempts"] == 1

        # Quiz 2
        q2 = client.post("/api/quizzes/generate", headers=headers, json={"document_id": doc_id, "topic": topic, "num_questions": 2}).json()
        # Submit all wrong -> 0%
        client.post(f"/api/quizzes/{q2['id']}/submit", headers=headers, json={"answers": {}})

        # Check mastery after Attempt 2:
        # Expected: 0.7 * 0 + 0.3 * 100.0 = 30.0%
        topic_prog2 = client.get(f"/api/progress/{topic}", headers=headers).json()
        assert topic_prog2["mastery_score"] == 30.0
        assert topic_prog2["quiz_attempts"] == 2
        assert topic_prog2["latest_score"] == 0.0

    # 14. Recommendation generation from learning signals
    def test_14_recommendation_generation(self, client: TestClient):
        headers, doc_id, _ = self.setup_user_with_document(client, "rec_gen")
        # Submit poor score to trigger Revision recommendation
        q = client.post("/api/quizzes/generate", headers=headers, json={"document_id": doc_id, "topic": "Subnetting", "num_questions": 2}).json()
        client.post(f"/api/quizzes/{q['id']}/submit", headers=headers, json={"answers": {}})

        # Fetch recommendations
        rec_res = client.get("/api/recommendations", headers=headers)
        assert rec_res.status_code == 200
        recs = rec_res.json()
        assert len(recs) >= 1
        assert any(r["topic"] == "Subnetting" for r in recs)
        assert any(r["recommendation_type"] in ["Revision", "Practice"] for r in recs)

    # 15. New user genuine zero/empty states
    def test_15_new_user_empty_states(self, client: TestClient):
        email = random_email("zero_state")
        token = client.post("/api/auth/register", json={"email": email, "password": "Password123!", "full_name": "Zero"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Progress summary: 0
        summary = client.get("/api/progress/summary", headers=headers).json()
        assert summary["total_questions_answered"] == 0
        assert summary["correct_answers"] == 0
        assert summary["average_mastery"] == 0.0
        assert summary["topics"] == []

        # Quizzes: empty list
        quizzes = client.get("/api/quizzes", headers=headers).json()
        assert quizzes == []

        # Recommendations: empty list
        recs = client.get("/api/recommendations", headers=headers).json()
        assert recs == []

        # Activity: empty list
        activity = client.get("/api/progress/activity", headers=headers).json()
        assert activity["activities"] == []

    # 16. Cross-user quiz isolation
    def test_16_cross_user_quiz_isolation(self, client: TestClient):
        headers_a, doc_a, _ = self.setup_user_with_document(client, "iso_a")
        headers_b, _, _ = self.setup_user_with_document(client, "iso_b")

        # User A creates a quiz
        quiz_a = client.post("/api/quizzes/generate", headers=headers_a, json={"document_id": doc_a, "topic": "Secret A", "num_questions": 2}).json()
        quiz_a_id = quiz_a["id"]

        # User B lists quizzes -> must NOT contain User A's quiz
        list_b = client.get("/api/quizzes", headers=headers_b).json()
        assert not any(q["id"] == quiz_a_id for q in list_b)

    # 17. Cross-user progress isolation
    def test_17_cross_user_progress_isolation(self, client: TestClient):
        headers_a, doc_a, _ = self.setup_user_with_document(client, "prog_iso_a")
        headers_b, _, _ = self.setup_user_with_document(client, "prog_iso_b")

        # User A generates & takes a quiz on unique topic
        topic_a = f"UniqueTopic_{uuid.uuid4().hex[:6]}"
        q_a = client.post("/api/quizzes/generate", headers=headers_a, json={"document_id": doc_a, "topic": topic_a, "num_questions": 2}).json()
        client.post(f"/api/quizzes/{q_a['id']}/submit", headers=headers_a, json={"answers": {}})

        # User B queries that topic -> 404 Not Found
        res_b = client.get(f"/api/progress/{topic_a}", headers=headers_b)
        assert res_b.status_code == 404

    # 18. Cross-user recommendation isolation
    def test_18_cross_user_recommendation_isolation(self, client: TestClient):
        headers_a, doc_a, _ = self.setup_user_with_document(client, "rec_iso_a")
        headers_b, _, _ = self.setup_user_with_document(client, "rec_iso_b")

        # User A has recommendation
        topic_a = f"TopicRec_{uuid.uuid4().hex[:6]}"
        q_a = client.post("/api/quizzes/generate", headers=headers_a, json={"document_id": doc_a, "topic": topic_a, "num_questions": 2}).json()
        client.post(f"/api/quizzes/{q_a['id']}/submit", headers=headers_a, json={"answers": {}})

        recs_a = client.get("/api/recommendations", headers=headers_a).json()
        assert len(recs_a) >= 1
        rec_a_id = recs_a[0]["id"]

        # User B gets recommendations -> does not contain User A's recommendation
        recs_b = client.get("/api/recommendations", headers=headers_b).json()
        assert not any(r["id"] == rec_a_id for r in recs_b)

        # User B directly tries to get User A's recommendation -> 404 Not Found
        direct_b = client.get(f"/api/recommendations/{rec_a_id}", headers=headers_b)
        assert direct_b.status_code == 404
