from typing import List, Dict, Any
from app.core.config import settings


def split_text_recursively(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: List[str] = None,
) -> List[str]:
    """
    Recursively split text into chunks of at most chunk_size characters with chunk_overlap.
    Tries splitting on paragraphs, lines, sentences, words, and characters.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # Find the highest priority separator present in the text
    chosen_sep = ""
    for sep in separators:
        if sep == "":
            chosen_sep = ""
            break
        if sep in text:
            chosen_sep = sep
            break

    splits = text.split(chosen_sep) if chosen_sep else list(text)

    chunks: List[str] = []
    current_chunk = ""

    for s in splits:
        candidate = f"{current_chunk}{chosen_sep}{s}" if current_chunk else s
        if len(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # If a single item is longer than chunk_size, split it with sub-separators
            if len(s) > chunk_size and len(separators) > 1:
                sub_separators = separators[separators.index(chosen_sep) + 1 :] if chosen_sep in separators else [""]
                sub_chunks = split_text_recursively(s, chunk_size, chunk_overlap, sub_separators)
                chunks.extend(sub_chunks[:-1] if sub_chunks else [])
                current_chunk = sub_chunks[-1] if sub_chunks else ""
            else:
                current_chunk = s

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Apply overlap merging if necessary
    if chunk_overlap > 0 and len(chunks) > 1:
        merged_chunks = []
        for i, ch in enumerate(chunks):
            if i == 0:
                merged_chunks.append(ch)
            else:
                prev = chunks[i - 1]
                overlap_text = prev[-chunk_overlap:] if len(prev) >= chunk_overlap else prev
                # Avoid exact duplicate prefix
                if not ch.startswith(overlap_text):
                    merged_chunks.append(f"... {ch}")
                else:
                    merged_chunks.append(ch)
        return merged_chunks

    return chunks


def chunk_extracted_pages(
    pages_data: List[Dict[str, Any]],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict[str, Any]]:
    """
    Process page text items into ordered chunks preserving page numbers and chunk_index.
    Returns list of dicts: {"chunk_index": int, "content": str, "page_number": int}
    """
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    all_chunks: List[Dict[str, Any]] = []
    global_index = 0

    for page in pages_data:
        page_num = page["page_number"]
        page_text = page["text"]
        
        page_chunks = split_text_recursively(page_text, chunk_size=size, chunk_overlap=overlap)
        for chunk_text in page_chunks:
            if chunk_text.strip():
                all_chunks.append({
                    "chunk_index": global_index,
                    "content": chunk_text,
                    "page_number": page_num,
                })
                global_index += 1

    return all_chunks
