import re
import os
from typing import Dict, List, Any, Optional

try:
    import pymupdf as fitz  # Modern PyMuPDF recommendation
except ImportError:
    import fitz


class PDFProcessor:
    """
    Production-ready PDF extraction service for BRSR / ESG reports using PyMuPDF.
    Extracts raw text page-by-page, performs semantic text normalization,
    and produces chunked segments tagged with page numbers for RAG retrieval.
    """

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        Cleans and normalizes extracted PDF text.
        Removes orphan hyphens, excessive whitespace, header/footer noise,
        and normalizes paragraph breaks.
        """
        if not raw_text:
            return ""

        # Normalize line-break hyphenation (e.g., "envi- \nronment" -> "environment")
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", raw_text)

        # Replace multiple newlines or tabs with consistent spacing
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)

        # Strip unprintable control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        return text.strip()

    @classmethod
    def extract_document(cls, file_path: str, chunk_size: int = 500, chunk_overlap: int = 100) -> Dict[str, Any]:
        """
        Extracts clean text page-by-page from a PDF file.

        Args:
            file_path: Absolute or relative path to the PDF.
            chunk_size: Approximate word/character window for chunking.
            chunk_overlap: Overlapping characters between consecutive chunks.

        Returns:
            Dictionary containing:
                - file_name: basename of file
                - total_pages: integer count
                - pages: list of page objects with page_num, clean_text, char_count
                - full_text: concatenated clean text
                - chunks: list of chunk objects with chunk_id, page_num, text
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        doc = fitz.open(file_path)
        total_pages = len(doc)
        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        chunks: List[Dict[str, Any]] = []
        chunk_id_counter = 1

        for page_idx in range(total_pages):
            page = doc.load_page(page_idx)
            raw_text = page.get_text("text") or ""
            clean = cls.clean_text(raw_text)

            pages_data.append({
                "page_num": page_idx + 1,
                "text": clean,
                "char_count": len(clean)
            })

            if clean:
                full_text_parts.append(f"--- [Page {page_idx + 1}] ---\n{clean}")

                # Create chunk passages tagged with page metadata for vector/keyword retrieval
                paragraphs = [p.strip() for p in clean.split("\n\n") if len(p.strip()) > 30]
                for p in paragraphs:
                    chunks.append({
                        "chunk_id": chunk_id_counter,
                        "page_num": page_idx + 1,
                        "text": p
                    })
                    chunk_id_counter += 1

        doc.close()

        return {
            "file_name": os.path.basename(file_path),
            "total_pages": total_pages,
            "pages": pages_data,
            "full_text": "\n\n".join(full_text_parts),
            "chunks": chunks
        }
