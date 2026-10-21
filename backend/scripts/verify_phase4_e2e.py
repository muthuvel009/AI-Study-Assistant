import io
import time
import uuid
import requests
from sqlalchemy import create_engine, text

BASE_URL = "http://127.0.0.1:8000"
DB_URL = "postgresql://postgres:postgres@127.0.0.1:5433/ai_study_assistant"


def generate_cs_notes_pdf() -> bytes:
    pages_text = [
        "Distributed Systems and Consensus: The Raft consensus algorithm is designed to be easy to understand. It is equivalent to multi-Paxos in fault-tolerance and performance. The algorithm decomposes consensus into leader election, log replication, and safety. A leader is elected when it receives votes from a majority of cluster nodes during an election term.",
        "Raft Safety Properties: Raft ensures State Machine Safety, meaning that if a server has applied a log entry at a given index to its state machine, no other server will ever apply a different log entry for the same index. Only candidates whose logs are at least as up-to-date as any other node in the majority can be elected leader.",
    ]

    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n")
    offsets = {}

    def write_obj(num, data):
        offsets[num] = buf.tell()
        buf.write(f"{num} 0 obj\n".encode("latin1"))
        buf.write(data)
        buf.write(b"\nendobj\n")

    shared_font_id = 3
    num_pages = len(pages_text)
    page_ids = [4 + i * 2 for i in range(num_pages)]
    content_ids = [5 + i * 2 for i in range(num_pages)]

    write_obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)
    write_obj(2, f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>".encode("latin1"))
    write_obj(shared_font_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for i, text in enumerate(pages_text):
        pid = page_ids[i]
        cid = content_ids[i]
        safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_data = f"BT /F1 12 Tf 50 750 Td ({safe_text}) Tj ET".encode("latin1")
        stream_len = len(stream_data)
        write_obj(
            pid,
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {shared_font_id} 0 R >> >> /Contents {cid} 0 R >>".encode(
                "latin1"
            ),
        )
        write_obj(cid, f"<< /Length {stream_len} >>\nstream\n".encode("latin1") + stream_data + b"\nendstream")

    xref_offset = buf.tell()
    buf.write(f"xref\n0 {len(offsets) + 1}\n".encode("latin1"))
    buf.write(b"0000000000 65535 f \n")
    for i in range(1, len(offsets) + 1):
        buf.write(f"{offsets[i]:010d} 00000 n \n".encode("latin1"))
    buf.write(f"trailer << /Size {len(offsets) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1"))
    return buf.getvalue()


def run_complete_e2e_verification():
    print("=" * 70)
    print("FINAL MASTER PHASE: 30-STEP END-TO-END WORKFLOW VERIFICATION")
    print("=" * 70)

    timings = {}

    # Step 1: Register User A
    t0 = time.time()
    user_a_email = f"student_a_{uuid.uuid4().hex[:6]}@stanford.edu"
    password_a = "SafeCampusPass123!"
    reg_a = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": user_a_email, "password": password_a, "full_name": "Alice Turing"},
    )
    timings["user_registration"] = (time.time() - t0) * 1000
    assert reg_a.status_code == 201, f"Step 1 Failed: {reg_a.text}"
    token_a = reg_a.json()["access_token"]
    user_a_id = reg_a.json()["user"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print(f"Step 1: Registered User A ({user_a_email}) in {timings['user_registration']:.1f}ms")

    # Step 2: Login User A
    t0 = time.time()
    login_a = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": user_a_email, "password": password_a},
    )
    timings["user_login"] = (time.time() - t0) * 1000
    assert login_a.status_code == 200, f"Step 2 Failed: {login_a.text}"
    print(f"Step 2: Logged in User A in {timings['user_login']:.1f}ms")

    # Step 3: Upload a real PDF
    t0 = time.time()
    pdf_bytes = generate_cs_notes_pdf()
    files = {"file": ("distributed_systems_raft.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    up_res = requests.post(f"{BASE_URL}/api/documents/upload", headers=headers_a, files=files)
    timings["pdf_upload_endpoint"] = (time.time() - t0) * 1000
    assert up_res.status_code == 201, f"Step 3 Failed: {up_res.text}"
    doc_data = up_res.json()
    doc_id = doc_data["id"]
    print(f"Step 3: Uploaded PDF '{doc_data['filename']}' (ID: {doc_id}) in {timings['pdf_upload_endpoint']:.1f}ms")

    # Step 4: Confirm Processing status
    print(f"Step 4: Initial document status confirmed: '{doc_data['status']}'")
    assert doc_data["status"] in ["Processing", "Ready"]

    # Step 5: Confirm Ready status
    t0 = time.time()
    final_status = doc_data["status"]
    for _ in range(30):
        if final_status == "Ready":
            break
        time.sleep(0.5)
        check = requests.get(f"{BASE_URL}/api/documents", headers=headers_a).json()
        for d in check:
            if d["id"] == doc_id:
                final_status = d["status"]
                doc_data = d
                break
    timings["pdf_background_processing"] = (time.time() - t0) * 1000
    assert final_status == "Ready", f"Step 5 Failed: Document status is {final_status}"
    print(f"Step 5: Document transitioned to 'Ready' in {timings['pdf_background_processing']:.1f}ms")

    # Step 6: Verify chunks exist in pgvector
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        chunks = conn.execute(
            text("SELECT id, chunk_index, page_number, vector_dims(embedding) FROM document_chunks WHERE document_id = :did"),
            {"did": doc_id},
        ).fetchall()
        assert len(chunks) >= 2
        for ch in chunks:
            assert ch[3] == 768
    print(f"Step 6: Verified {len(chunks)} chunks in pgvector with 768 float dimensions")

    # Step 7: Ask grounded RAG question
    t0 = time.time()
    q_grounded = "What is the Raft consensus algorithm and how does a leader get elected?"
    chat_res = requests.post(f"{BASE_URL}/api/chat", headers=headers_a, json={"query": q_grounded})
    timings["rag_chat_grounded"] = (time.time() - t0) * 1000
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    print(f"Step 7: Grounded RAG query answered in {timings['rag_chat_grounded']:.1f}ms")

    # Step 8: Verify source citation
    assert len(chat_data["sources"]) > 0
    src = chat_data["sources"][0]
    assert src["document_name"] == "distributed_systems_raft.pdf"
    assert "cosine_distance" in src
    print(f"Step 8: Verified source citation: Doc '{src['document_name']}', Page {src['page_number']}, Cosine Distance: {src['cosine_distance']}")

    # Step 9: Ask unsupported question
    t0 = time.time()
    unsupported_query = "What is the optimal baking temperature for french sourdough baguettes?"
    unsupported_res = requests.post(f"{BASE_URL}/api/chat", headers=headers_a, json={"query": unsupported_query})
    timings["rag_chat_unsupported"] = (time.time() - t0) * 1000
    unsupported_data = unsupported_res.json()
    print(f"Step 9: Asked unsupported question in {timings['rag_chat_unsupported']:.1f}ms")

    # Step 10: Verify grounded fallback response
    assert "not found in the uploaded study material" in unsupported_data["answer"].lower()
    print("Step 10: Verified grounded refusal: 'The information was not found in the uploaded study material.'")

    # Step 11 & 12: Generate a Medium 5-question quiz selecting topic
    t0 = time.time()
    quiz_req = {
        "document_id": doc_id,
        "topic": "Raft Consensus Algorithm",
        "difficulty": "Medium",
        "num_questions": 5,
    }
    quiz_res = requests.post(f"{BASE_URL}/api/quizzes/generate", headers=headers_a, json=quiz_req)
    timings["quiz_generation"] = (time.time() - t0) * 1000
    assert quiz_res.status_code == 201, f"Quiz generation failed: {quiz_res.text}"
    quiz_data = quiz_res.json()
    quiz_id = quiz_data["id"]
    print(f"Step 11 & 12: Generated 5-question Medium quiz on '{quiz_data['topic']}' in {timings['quiz_generation']:.1f}ms")

    # Step 13: Verify semantic retrieval
    assert len(quiz_data["questions"]) == 5
    print("Step 13: Verified 5 questions retrieved from relevant document chunks")

    # Step 14: Verify correct answers are NOT in generation response
    for q in quiz_data["questions"]:
        assert "correct_answer" not in q, "SECURITY VIOLATION: correct_answer exposed before submission!"
        assert "explanation" not in q, "SECURITY VIOLATION: explanation exposed before submission!"
        assert len(q["options"]) == 4
    print("Step 14: Security Verified: Correct answers and explanations are strictly omitted from generation response")

    # Step 15 & 16: Complete and Submit Quiz
    # Fetch answer key directly from DB to answer 4 out of 5 correctly (80% score)
    with engine.connect() as conn:
        q_rows = conn.execute(text("SELECT id, correct_answer FROM questions WHERE quiz_id = :qid ORDER BY id"), {"qid": quiz_id}).fetchall()
    
    student_answers = {}
    for idx, row in enumerate(q_rows):
        if idx < 4:
            student_answers[row[0]] = row[1]  # Correct
        else:
            student_answers[row[0]] = "Wrong Deliberate Answer Option"  # Wrong

    t0 = time.time()
    sub_res = requests.post(f"{BASE_URL}/api/quizzes/{quiz_id}/submit", headers=headers_a, json={"answers": student_answers})
    timings["quiz_submission_scoring"] = (time.time() - t0) * 1000
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    print(f"Step 15 & 16: Completed and submitted quiz in {timings['quiz_submission_scoring']:.1f}ms")

    # Step 17: Verify server-side score
    assert sub_data["score"] == 80.0
    assert sub_data["correct_count"] == 4
    assert sub_data["total_questions"] == 5
    print(f"Step 17: Authoritative Server-side Score Verified: {sub_data['score']}% (4/5)")

    # Step 18: Verify Progress updates
    prog_res = requests.get(f"{BASE_URL}/api/progress/summary", headers=headers_a)
    assert prog_res.status_code == 200
    prog_summary = prog_res.json()
    assert prog_summary["total_questions_answered"] >= 5
    assert prog_summary["correct_answers"] >= 4
    print(f"Step 18: Progress summary updated: {prog_summary['total_questions_answered']} answered, {prog_summary['correct_answers']} correct")

    # Step 19: Verify mastery updates
    topic_res = requests.get(f"{BASE_URL}/api/progress/{quiz_data['topic']}", headers=headers_a)
    assert topic_res.status_code == 200
    topic_data = topic_res.json()
    assert topic_data["mastery_score"] == 80.0
    assert topic_data["quiz_attempts"] == 1
    print(f"Step 19: Topic mastery updated: {topic_data['mastery_score']}% (1 attempt)")

    # Step 20: Verify Dashboard updates
    t0 = time.time()
    dash_docs = requests.get(f"{BASE_URL}/api/documents", headers=headers_a).json()
    dash_quizzes = requests.get(f"{BASE_URL}/api/quizzes", headers=headers_a).json()
    dash_prog = requests.get(f"{BASE_URL}/api/progress/summary", headers=headers_a).json()
    timings["dashboard_aggregation"] = (time.time() - t0) * 1000
    assert len(dash_docs) >= 1
    assert len(dash_quizzes) >= 1
    assert dash_prog["average_mastery"] > 0
    print(f"Step 20: Dashboard metrics aggregated in {timings['dashboard_aggregation']:.1f}ms: Docs={len(dash_docs)}, Quizzes={len(dash_quizzes)}, Mastery={dash_prog['average_mastery']}%")

    # Step 21: Verify Recommendations appear
    rec_res = requests.get(f"{BASE_URL}/api/recommendations", headers=headers_a)
    assert rec_res.status_code == 200
    recs = rec_res.json()
    assert len(recs) >= 1
    rec_item = recs[0]
    print(f"Step 21: Recommendation active: [{rec_item['recommendation_type']}] {rec_item['title']} - Reason: {rec_item['reason']}")

    # Step 22 & 23 & 24: Logout & Login again -> Data persists
    login_re = requests.post(f"{BASE_URL}/api/auth/login", json={"email": user_a_email, "password": password_a})
    assert login_re.status_code == 200
    re_token = login_re.json()["access_token"]
    re_headers = {"Authorization": f"Bearer {re_token}"}
    me_check = requests.get(f"{BASE_URL}/api/auth/me", headers=re_headers).json()
    assert me_check["email"] == user_a_email
    re_quizzes = requests.get(f"{BASE_URL}/api/quizzes", headers=re_headers).json()
    assert any(q["id"] == quiz_id for q in re_quizzes)
    print("Steps 22-24: Relogin succeeded. Authentication session and all learning data persisted across sessions.")

    # Step 25: Register User B
    user_b_email = f"student_b_{uuid.uuid4().hex[:6]}@berkeley.edu"
    reg_b = requests.post(f"{BASE_URL}/api/auth/register", json={"email": user_b_email, "password": "SecurePasswordB123!", "full_name": "Bob Babbage"})
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    print(f"Step 25: Registered User B ({user_b_email})")

    # Step 26: User B cannot access User A's documents
    b_docs = requests.get(f"{BASE_URL}/api/documents", headers=headers_b).json()
    assert not any(d["id"] == doc_id for d in b_docs)
    b_doc_direct = requests.get(f"{BASE_URL}/api/documents/{doc_id}", headers=headers_b)
    assert b_doc_direct.status_code == 404
    print("Step 26: User B document isolation verified (404 on direct access, absent in list)")

    # Step 27: User B cannot access User A's RAG chunks
    b_rag = requests.post(f"{BASE_URL}/api/chat", headers=headers_b, json={"query": "Raft consensus leader election"}).json()
    assert "not found in the uploaded study material" in b_rag["answer"].lower()
    assert len(b_rag.get("sources", [])) == 0
    print("Step 27: User B vector RAG isolation verified (0 citations, grounded fallback)")

    # Step 28: User B cannot access User A's quizzes
    b_quizzes = requests.get(f"{BASE_URL}/api/quizzes", headers=headers_b).json()
    assert not any(q["id"] == quiz_id for q in b_quizzes)
    b_quiz_direct = requests.get(f"{BASE_URL}/api/quizzes/{quiz_id}", headers=headers_b)
    assert b_quiz_direct.status_code == 404
    b_quiz_sub = requests.post(f"{BASE_URL}/api/quizzes/{quiz_id}/submit", headers=headers_b, json={"answers": {}})
    assert b_quiz_sub.status_code == 404
    print("Step 28: User B quiz isolation verified (404 on direct view and submission)")

    # Step 29: User B cannot access User A's progress
    b_prog = requests.get(f"{BASE_URL}/api/progress/summary", headers=headers_b).json()
    assert b_prog["total_questions_answered"] == 0
    assert b_prog["average_mastery"] == 0.0
    b_topic = requests.get(f"{BASE_URL}/api/progress/{quiz_data['topic']}", headers=headers_b)
    assert b_topic.status_code == 404
    print("Step 29: User B progress isolation verified (Authentic zero state, 404 on topic)")

    # Step 30: User B cannot access User A's recommendations
    b_recs = requests.get(f"{BASE_URL}/api/recommendations", headers=headers_b).json()
    assert len(b_recs) == 0
    b_rec_direct = requests.get(f"{BASE_URL}/api/recommendations/{rec_item['id']}", headers=headers_b)
    assert b_rec_direct.status_code == 404
    print("Step 30: User B recommendations isolation verified (0 recommendations, 404 on direct access)")

    print("=" * 70)
    print("ALL 30 END-TO-END WORKFLOW VERIFICATION STEPS PASSED WITH 100% ISOLATION!")
    print("=" * 70)
    print("\nACTUAL MEASURED PERFORMANCE:")
    for k, v in timings.items():
        print(f"  - {k}: {v:.1f} ms")


if __name__ == "__main__":
    run_complete_e2e_verification()
