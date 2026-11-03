from __future__ import annotations
import io
import re
from typing import List, Tuple, Optional
from collections import Counter
from pypdf import PdfReader
from app.models import ExtractionResult

# Common English stop words to filter out when generating tags
STOP_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "she", "or", "an", "will", "my", "one", "all", "would", "there",
    "their", "what", "so", "up", "out", "if", "about", "who", "get",
    "which", "go", "me", "when", "make", "can", "like", "time", "no",
    "just", "him", "know", "take", "people", "into", "year", "your",
    "good", "some", "could", "them", "see", "other", "than", "then",
    "now", "look", "only", "come", "its", "over", "think", "also"
}


def _extract_tags_from_text(text: str, max_tags: int = 5) -> List[str]:
    """Extract top frequent significant words as tags."""
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    filtered_words = [w for w in words if w not in STOP_WORDS]
    if not filtered_words:
        return ["untagged"]
    counts = Counter(filtered_words)
    return [word for word, _ in counts.most_common(max_tags)]


def _simulate_ocr_for_image_or_binary(filename: str, file_bytes: bytes) -> Tuple[str, List[str]]:
    """Simulated OCR fallback for image/binary files where direct text extraction is not applicable."""
    file_size_kb = len(file_bytes) // 1024
    simulated_text = (
        f"Simulated OCR document scan for file {filename}. "
        f"Detected high contrast scanned content spanning approximate size {file_size_kb} KB. "
        f"Processed via Google Cloud Serverless OCR Simulation Engine."
    )
    tags = ["ocr_simulated", "scanned_document"]
    clean_name = filename.replace("_", " ").replace("-", " ").replace(".", " ")
    name_keywords = re.findall(r"\b[a-zA-Z]{3,}\b", clean_name.lower())
    for kw in name_keywords:
        if kw not in tags and kw not in STOP_WORDS and kw not in {"png", "jpg", "jpeg", "tiff", "bmp", "pdf"}:
            tags.append(kw)
    return simulated_text, tags[:5]


def process_document(filename: str, content_type: str | None, file_bytes: bytes) -> ExtractionResult:
    """
    Extracts text, word count, and tags from document bytes.
    Supports PDFs and plain text directly; falls back to simulated OCR for images/other formats.
    """
    filename_lower = filename.lower()
    content_type_lower = (content_type or "").lower()

    # 1. Plain text / CSV / Markdown files
    if (
        filename_lower.endswith((".txt", ".md", ".csv", ".json", ".log"))
        or "text/" in content_type_lower
    ):
        try:
            text = file_bytes.decode("utf-8", errors="replace")
            words = text.split()
            word_count = len(words)
            tags = _extract_tags_from_text(text)
            return ExtractionResult(
                text=text,
                word_count=word_count,
                tags=tags,
                ocr_simulated=False,
            )
        except Exception:
            pass  # Fall through to simulated OCR

    # 2. PDF files
    if filename_lower.endswith(".pdf") or "application/pdf" in content_type_lower:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            extracted_pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text)
            
            full_text = "\n".join(extracted_pages).strip()
            
            if full_text:
                words = full_text.split()
                return ExtractionResult(
                    text=full_text,
                    word_count=len(words),
                    tags=_extract_tags_from_text(full_text),
                    ocr_simulated=False,
                )
        except Exception:
            pass  # If PDF parsing fails or is scanned image PDF, fall back to simulated OCR

    # 3. Simulated OCR Fallback (Images, scans, binary documents)
    simulated_text, tags = _simulate_ocr_for_image_or_binary(filename, file_bytes)
    word_count = len(simulated_text.split())
    return ExtractionResult(
        text=simulated_text,
        word_count=word_count,
        tags=tags,
        ocr_simulated=True,
    )
