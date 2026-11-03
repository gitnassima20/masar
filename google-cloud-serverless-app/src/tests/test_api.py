import json
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app, gcs_helper, bq_writer

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_handle_cloudevent_success(monkeypatch):
    # Mock GCS helper download
    mock_file_content = b"Financial report for Q3. Revenue increased by 20% year over year."
    monkeypatch.setattr(gcs_helper, "download_file_bytes", MagicMock(return_value=mock_file_content))
    
    # Mock BigQuery write
    mock_bq_insert = MagicMock()
    monkeypatch.setattr(bq_writer, "insert_record", mock_bq_insert)

    cloudevent_payload = {
        "bucket": "input-docs-bucket",
        "name": "reports/q3_financials.txt",
        "contentType": "text/plain",
        "size": "65",
        "timeCreated": "2026-11-03T10:00:00Z",
        "generation": "1730628000123456"
    }

    headers = {
        "ce-id": "evt-12345",
        "ce-source": "//storage.googleapis.com/projects/_/buckets/input-docs-bucket",
        "ce-specversion": "1.0",
        "ce-type": "google.cloud.storage.object.v1.finalized",
        "Content-Type": "application/json"
    }

    response = client.post("/", headers=headers, json=cloudevent_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["file_name"] == "reports/q3_financials.txt"
    assert data["ocr_simulated"] is False
    assert mock_bq_insert.called
