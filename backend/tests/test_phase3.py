import io
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Document, DocumentChunk, Chat, Message
from app.services.pdf_service import extract_pdf_pages
from app.services.chunking_service import chunk_extracted_pages, split_text_recursively
from app.services.ai_service import generate_embedding, generate_embeddings_batch, generate_rag_answer
from app.services.processing_service import process_document_background


def generate_valid_pdf_bytes(pages_text: list[str]) -> bytes:
    """Helper to generate valid multi-page PDF bytes in memory for tests."""
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


def random_email(prefix="p3_user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@university.edu"


class TestPhase3RAGPipeline:

    # 1. PDF Text Extraction & page numbers
    def test_01_pdf_text_extraction(self, tmp_path):
        page_texts = [
            "Photosynthesis occurs in plant chloroplasts using chlorophyll to capture sunlight.",
            "Cellular respiration takes place in the mitochondria and produces adenosine triphosphate.",
        ]
        pdf_bytes = generate_valid_pdf_bytes(page_texts)
        pdf_file = tmp_path / "biology_notes.pdf"
        pdf_file.write_bytes(pdf_bytes)

        pages = extract_pdf_pages(str(pdf_file))
        assert len(pages) == 2
        assert pages[0]["page_number"] == 1
        assert "Photosynthesis" in pages[0]["text"]
        assert pages[1]["page_number"] == 2
        assert "Cellular respiration" in pages[1]["text"]

    # 2. Recursive Chunking with overlap and sequence
    def test_02_recursive_chunking(self):
        pages_data = [
            {
                "page_number": 1,
                "text": "Introduction to Linear Algebra. Vectors and matrices represent transformations in multidimensional spaces. " * 15,
            },
            {
                "page_number": 2,
                "text": "Eigenvalues and Eigenvectors. An eigenvector does not change direction when a linear transformation is applied. " * 15,
            },
        ]
        chunks = chunk_extracted_pages(pages_data, chunk_size=300, chunk_overlap=50)
        assert len(chunks) > 2
        for idx, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == idx
            assert chunk["page_number"] in [1, 2]
            assert len(chunk["content"]) > 0

    # 3. Embedding Generation (768 dimensions)
    def test_03_embedding_generation_768_dim(self):
        emb = generate_embedding("What is dynamic programming?")
        assert isinstance(emb, list)
        assert len(emb) == 768
        assert all(isinstance(x, float) for x in emb)

        batch_embs = generate_embeddings_batch(["Algorithm 1", "Algorithm 2"])
        assert len(batch_embs) == 2
        assert len(batch_embs[0]) == 768
        assert len(batch_embs[1]) == 768

    # 4. Document upload returns 201 with 'Processing' status
    def test_04_document_upload_returns_processing(self, client: TestClient):
        email = random_email("upload_test")
        reg = client.post("/api/auth/register", json={"email": email, "password": "Password123!", "full_name": "Uploader"})
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        pdf_bytes = generate_valid_pdf_bytes(["Test document content for upload test."])
        files = {"file": ("test_upload.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

        response = client.post("/api/documents/upload", headers=headers, files=files)
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test_upload.pdf"
        assert data["status"] in ["Processing", "Ready"]
        assert "id" in data

    # 5. Background processing transitions to 'Ready' and populates chunks + embeddings
    def test_05_background_processing_transitions_to_ready(self, client: TestClient):
        email = random_email("bg_ready")
        reg = client.post("/api/auth/register", json={"email": email, "password": "Password123!", "full_name": "Bg Processor"})
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        doc_content = [
            "Data structures include arrays, linked lists, stacks, and queues.",
            "Trees and graphs provide hierarchical and relational modeling capabilities.",
        ]
        pdf_bytes = generate_valid_pdf_bytes(doc_content)
        files = {"file": ("data_structures.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

        upload_res = client.post("/api/documents/upload", headers=headers, files=files)
        assert upload_res.status_code == 201
        doc_id = upload_res.json()["id"]

        # Run processing synchronously to verify transition to Ready
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            assert doc is not None
            process_document_background(doc.id, doc.file_path)

            db.refresh(doc)
            assert doc.status == "Ready"
            assert doc.chunks_count > 0

            # Verify chunks in database
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
            assert len(chunks) == doc.chunks_count
            for chunk in chunks:
                assert chunk.embedding is not None
                assert len(chunk.embedding) == 768
                assert chunk.page_number in [1, 2]
        finally:
            db.close()

    # 6. Corrupted/Empty PDF transitions to 'Failed'
    def test_06_corrupted_empty_pdf_transitions_to_failed(self, client: TestClient, tmp_path):
        email = random_email("fail_test")
        reg = client.post("/api/auth/register", json={"email": email, "password": "Password123!", "full_name": "Fail Tester"})
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Upload non-PDF junk
        corrupt_bytes = b"NOT_A_REAL_PDF_DATA_STREAM"
        files = {"file": ("corrupted.pdf", io.BytesIO(corrupt_bytes), "application/pdf")}

        upload_res = client.post("/api/documents/upload", headers=headers, files=files)
        assert upload_res.status_code == 201
        doc_id = upload_res.json()["id"]

        # Run background processing
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            process_document_background(doc.id, doc.file_path)
            db.refresh(doc)
            assert doc.status == "Failed"
            assert doc.chunks_count == 0
        finally:
            db.close()

    # 7. pgvector cosine similarity search
    def test_07_pgvector_cosine_distance_search(self):
        db = SessionLocal()
        try:
            # Query chunks ordered by cosine distance
            query_emb = generate_embedding("Data structures like trees and graphs")
            stmt = select(DocumentChunk).order_by(DocumentChunk.embedding.cosine_distance(query_emb)).limit(3)
            results = db.execute(stmt).scalars().all()
            assert len(results) > 0
            assert results[0].content is not None
        finally:
            db.close()

    # 8. Grounded RAG response with citations
    def test_08_grounded_rag_response_with_citations(self, client: TestClient):
        email = random_email("rag_student")
        reg = client.post("/api/auth/register", json={"email": email, "password": "Password123!", "full_name": "RAG Student"})
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        content = [
            "The capital of Australia is Canberra. It was selected as a compromise between Sydney and Melbourne in 1908.",
            "Canberra is a planned city designed by American architects Walter Burley Griffin and Marion Mahony Griffin.",
        ]
        pdf_bytes = generate_valid_pdf_bytes(content)
        files = {"file": ("australia_geography.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

        upload_res = client.post("/api/documents/upload", headers=headers, files=files)
        doc_id = upload_res.json()["id"]

        # Process document
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            process_document_background(doc.id, doc.file_path)
        finally:
            db.close()

        # Query chat endpoint
        chat_res = client.post(
            "/api/chat",
            headers=headers,
            json={"query": "What is the capital of Australia and why was it chosen?"},
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert "Canberra" in data["answer"]
        assert len(data["sources"]) > 0
        source = data["sources"][0]
        assert source["document_name"] == "australia_geography.pdf"
        assert source["page_number"] in [1, 2]
        assert "chunk_id" in source

    # 9. Grounded RAG handles unrelated query
    def test_09_grounded_rag_unrelated_query(self, client: TestClient):
        email = random_email("unrelated_query")
        reg = client.post("/api/auth/register", json={"email": email, "password": "Password123!", "full_name": "Query Tester"})
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        content = ["Microeconomics studies how individuals and firms allocate scarce resources."]
        pdf_bytes = generate_valid_pdf_bytes(content)
        files = {"file": ("economics.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

        upload_res = client.post("/api/documents/upload", headers=headers, files=files)
        doc_id = upload_res.json()["id"]

        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            process_document_background(doc.id, doc.file_path)
        finally:
            db.close()

        # Query for something completely unrelated
        chat_res = client.post(
            "/api/chat",
            headers=headers,
            json={"query": "Explain quantum entanglement and quantum teleportation algorithms."},
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        # When similarity distance exceeds threshold or context doesn't answer, returns strict fallback
        assert "not found" in data["answer"].lower() or len(data["sources"]) == 0

    # 10. Cross-user RAG isolation
    def test_10_cross_user_rag_isolation(self, client: TestClient):
        # User Alpha
        email_alpha = random_email("user_alpha")
        token_alpha = client.post(
            "/api/auth/register", json={"email": email_alpha, "password": "Password123!", "full_name": "Alpha"}
        ).json()["access_token"]
        headers_alpha = {"Authorization": f"Bearer {token_alpha}"}

        # User Beta
        email_beta = random_email("user_beta")
        token_beta = client.post(
            "/api/auth/register", json={"email": email_beta, "password": "Password123!", "full_name": "Beta"}
        ).json()["access_token"]
        headers_beta = {"Authorization": f"Bearer {token_beta}"}

        # User Alpha uploads secret research
        alpha_text = ["Project SuperSecretCodeName: The key code to open the vault is Omega-99214."]
        alpha_pdf = generate_valid_pdf_bytes(alpha_text)
        res_a = client.post("/api/documents/upload", headers=headers_alpha, files={"file": ("vault_secrets.pdf", io.BytesIO(alpha_pdf), "application/pdf")})
        doc_a_id = res_a.json()["id"]

        db = SessionLocal()
        try:
            doc_a = db.query(Document).filter(Document.id == doc_a_id).first()
            process_document_background(doc_a.id, doc_a.file_path)
        finally:
            db.close()

        # User Beta queries about the vault code
        beta_query = client.post(
            "/api/chat",
            headers=headers_beta,
            json={"query": "What is the key code to open the vault in Project SuperSecretCodeName?"},
        )
        assert beta_query.status_code == 200
        beta_data = beta_query.json()
        # Beta must NOT retrieve Alpha's secret chunk
        assert "Omega-99214" not in beta_data["answer"]
        assert not any(s["document_name"] == "vault_secrets.pdf" for s in beta_data.get("sources", []))

    # 11. Unauthorized document and chat access
    def test_11_unauthorized_document_and_chat_access(self, client: TestClient):
        # No token
        res_docs = client.get("/api/documents")
        assert res_docs.status_code == 401

        res_chat = client.post("/api/chat", json={"query": "Hello"})
        assert res_chat.status_code == 401

        res_history = client.get("/api/chat/history")
        assert res_history.status_code == 401

    # 12. Offline fallback handling in ai_service
    def test_12_offline_fallback_handling(self):
        # Even with empty context or fallback generation, returns valid structure
        empty_res = generate_rag_answer("Is this covered?", [])
        assert "not found in the uploaded study material" in empty_res["answer"].lower()
        assert empty_res["sources"] == []

        # With mock chunk
        single_chunk = [{"content": "Robotics involves kinematics and dynamics of rigid bodies.", "page_number": 1, "document_name": "robotics.pdf"}]
        res = generate_rag_answer("What does robotics involve?", single_chunk)
        assert len(res["answer"]) > 0
        assert len(res["sources"]) == 1
