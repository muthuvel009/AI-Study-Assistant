import io
import time
import uuid
import requests
from sqlalchemy import create_engine, text

BASE_URL = "http://127.0.0.1:8000"
DB_URL = "postgresql://postgres:postgres@127.0.0.1:5433/ai_study_assistant"


def generate_os_pdf() -> bytes:
    pages_text = [
        "Operating Systems: Memory Management. Paging is a memory management scheme that eliminates the need for contiguous allocation of physical memory. The physical address space of a process can be noncontiguous. Physical memory is broken into fixed-sized blocks called frames. Logical memory is broken into blocks of the same size called pages.",
        "Page Fault Handling: When a process tries to access a page that is not currently mapped in physical RAM, the Memory Management Unit triggers a page fault exception. The operating system traps to kernel mode, finds a free frame on the backing store, reads the required page from disk into the frame, updates the page table, and restarts the instruction that caused the trap.",
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


def run_live_verification():
    print("=" * 60)
    print("PHASE 3 LIVE END-TO-END RAG PIPELINE VERIFICATION")
    print("=" * 60)

    # 1. Health check
    h = requests.get(f"{BASE_URL}/health")
    print(f"1. Health check: {h.status_code} -> {h.json()}")
    assert h.status_code == 200

    # 2. Register User A
    user_a_email = f"student_a_{uuid.uuid4().hex[:6]}@mit.edu"
    reg_a = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": user_a_email, "password": "SecurePassword123!", "full_name": "Alice Cooper"},
    )
    assert reg_a.status_code == 201, f"User A registration failed: {reg_a.text}"
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print(f"2. Registered User A: {user_a_email}")

    # 3. Upload PDF
    pdf_bytes = generate_os_pdf()
    files = {"file": ("operating_systems_notes.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    t0 = time.time()
    up_res = requests.post(f"{BASE_URL}/api/documents/upload", headers=headers_a, files=files)
    upload_duration = time.time() - t0
    assert up_res.status_code == 201, f"Upload failed: {up_res.text}"
    doc_data = up_res.json()
    doc_id = doc_data["id"]
    print(f"3. Uploaded PDF: {doc_data['filename']} (ID: {doc_id}) in {upload_duration*1000:.1f}ms")
    print(f"   Initial status: {doc_data['status']}")

    # 4. Poll until Ready
    print("4. Polling for background chunking & embedding processing...")
    processing_start = time.time()
    final_status = doc_data["status"]
    for _ in range(30):
        if final_status == "Ready":
            break
        time.sleep(0.5)
        check = requests.get(f"{BASE_URL}/api/documents", headers=headers_a)
        for d in check.json():
            if d["id"] == doc_id:
                final_status = d["status"]
                doc_data = d
                break
    processing_duration = time.time() - processing_start
    print(f"   Document final status: {final_status}")
    print(f"   Chunks count: {doc_data.get('chunks_count')}")
    print(f"   Processing duration: {processing_duration*1000:.1f}ms")
    assert final_status == "Ready", f"Expected Ready, got {final_status}"
    assert doc_data.get("chunks_count", 0) > 0

    # 5. Database Direct Verification (PostgreSQL & pgvector)
    print("5. Direct PostgreSQL pgvector inspection:")
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT chunk_index, page_number, length(content) as char_len, "
                "vector_dims(embedding) as dim FROM document_chunks WHERE document_id = :did ORDER BY chunk_index"
            ),
            {"did": doc_id},
        ).fetchall()
        for row in result:
            print(f"   Chunk #{row[0]}: Page {row[1]}, Characters: {row[2]}, Vector Dimension: {row[3]}")
            assert row[3] == 768, f"Expected 768 dimensions, got {row[3]}"

    # 6. Live RAG Chat Query: Grounded Question
    print("6. Executing Grounded RAG Chat Query:")
    t_chat = time.time()
    query_text = "What is paging and how does page fault handling work?"
    chat_res = requests.post(f"{BASE_URL}/api/chat", headers=headers_a, json={"query": query_text})
    rag_duration = time.time() - t_chat
    assert chat_res.status_code == 200, f"Chat failed: {chat_res.text}"
    chat_data = chat_res.json()
    print(f"   Question: '{query_text}'")
    print(f"   RAG Total Latency: {rag_duration*1000:.1f}ms")
    print(f"   Answer:\n{chat_data['answer']}\n")
    print(f"   Sources cited ({len(chat_data['sources'])}):")
    for s in chat_data["sources"]:
        print(f"     - Doc: '{s['document_name']}', Page {s['page_number']}, Similarity: {s['similarity']}")
    assert len(chat_data["sources"]) > 0
    assert any("page fault" in s["snippet"].lower() or "paging" in s["snippet"].lower() for s in chat_data["sources"])

    # 7. Unrelated Query: Hallucination Prevention
    print("7. Testing Hallucination Prevention on Unrelated Query:")
    unrelated_res = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers_a,
        json={"query": "What are the rules of American Football and how many points is a touchdown?"},
    )
    unrelated_data = unrelated_res.json()
    print(f"   Answer: {unrelated_data['answer']}")
    print(f"   Sources: {unrelated_data['sources']}")
    assert "not found in the uploaded study material" in unrelated_data["answer"].lower() or len(unrelated_data["sources"]) == 0

    # 8. User B Cross-User Isolation
    print("8. Testing Multi-Tenant Cross-User Isolation:")
    user_b_email = f"student_b_{uuid.uuid4().hex[:6]}@harvard.edu"
    reg_b = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": user_b_email, "password": "SecurePassword456!", "full_name": "Bob Dylan"},
    )
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B asks about User A's document topic
    query_b = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers_b,
        json={"query": "What is paging and how does page fault handling work?"},
    )
    b_data = query_b.json()
    print(f"   User B query answer: {b_data['answer']}")
    print(f"   User B citations count: {len(b_data['sources'])}")
    # User B must NOT receive any chunks or citations to User A's document
    assert not any(s["document_name"] == "operating_systems_notes.pdf" for s in b_data.get("sources", []))
    assert len(b_data.get("sources", [])) == 0

    print("=" * 60)
    print("ALL LIVE END-TO-END RAG CHECKS PASSED WITH FULL ISOLATION!")
    print("=" * 60)


if __name__ == "__main__":
    run_live_verification()
