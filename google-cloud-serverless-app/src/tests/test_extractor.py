from app.extractor import process_document, _extract_tags_from_text


def test_extract_tags_from_text():
    sample_text = (
        "Serverless architecture on Google Cloud Platform offers high scalability, "
        "low latency, and reliable event-driven pipeline design. Architecture scalability."
    )
    tags = _extract_tags_from_text(sample_text, max_tags=3)
    assert len(tags) <= 3
    assert "scalability" in tags or "architecture" in tags


def test_process_plain_text():
    content = b"Invoice #10492 for Acme Corp. Total payment due: $500. Due date tomorrow."
    result = process_document("invoice.txt", "text/plain", content)
    assert result.ocr_simulated is False
    assert result.word_count == 12
    assert "invoice" in result.tags or "acme" in result.tags


def test_process_simulated_ocr_for_image():
    # Simulated png image bytes
    image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 2048
    result = process_document("receipt_scan.png", "image/png", image_bytes)
    assert result.ocr_simulated is True
    assert result.word_count > 0
    assert "ocr_simulated" in result.tags
    assert "scanned_document" in result.tags
    assert "receipt" in result.tags
