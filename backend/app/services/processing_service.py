import traceback
from app.db.database import SessionLocal
from app.db.models import Document, DocumentChunk
from app.services.pdf_service import extract_pdf_pages
from app.services.chunking_service import chunk_extracted_pages
from app.services.ai_service import generate_embedding


def process_document_background(document_id: str, file_path: str):
    """
    Safely process an uploaded PDF in the background:
    1. Fresh database session (SessionLocal)
    2. Extract text & page numbers using pypdf
    3. Split into recursive chunks
    4. Generate embeddings via Gemini / AI service
    5. Bulk save chunks to database with pgvector
    6. Transition document status from 'Processing' to 'Ready' (or 'Failed' on error)
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            print(f"[Background Processor] Document {document_id} not found in database.")
            return

        # 1. Extract text and authentic page numbers from PDF
        pages_data = extract_pdf_pages(file_path)

        # 2. Chunk pages recursively with overlap
        chunks_data = chunk_extracted_pages(pages_data)

        if not chunks_data:
            raise ValueError("No valid text chunks could be produced from document.")

        # 3. Clean any existing chunks for this document (e.g. on re-processing)
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()

        # 4. Generate embeddings and create DocumentChunk entities
        chunk_entities = []
        for c in chunks_data:
            emb = generate_embedding(c["content"])
            chunk_entity = DocumentChunk(
                document_id=document_id,
                chunk_index=c["chunk_index"],
                content=c["content"],
                page_number=c["page_number"],
                embedding=emb,
            )
            chunk_entities.append(chunk_entity)

        # 5. Bulk insert chunks
        db.bulk_save_objects(chunk_entities)

        # 6. Update Document status to 'Ready'
        doc.status = "Ready"
        doc.chunks_count = len(chunk_entities)
        db.commit()
        print(f"[Background Processor] Document {document_id} processed successfully ({len(chunk_entities)} chunks).")

    except Exception as e:
        db.rollback()
        print(f"[Background Processor] Error processing document {document_id}: {e}")
        traceback.print_exc()
        try:
            # Mark document as Failed so it is never permanently stuck in 'Processing'
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "Failed"
                db.commit()
        except Exception as update_err:
            print(f"[Background Processor] Failed to update document status to 'Failed': {update_err}")
    finally:
        db.close()
