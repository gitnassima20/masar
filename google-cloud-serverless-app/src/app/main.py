import logging
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from cloudevents.http import from_http

from app.config import settings
from app.models import StorageObjectData, DocumentMetadataRecord
from app.extractor import process_document
from app.gcs_client import GCSHelper
from app.bq_writer import BigQueryWriter

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("document-pipeline")

app = FastAPI(
    title="Serverless Document Processing Pipeline",
    description="Eventarc/Cloud Run service to process GCS documents and stream metadata to BigQuery",
    version="1.0.0"
)

# Dependency helpers (instantiated lazily or overridden in tests)
gcs_helper = GCSHelper()
bq_writer = BigQueryWriter(
    project_id=settings.gcp_project,
    dataset_id=settings.bq_dataset_id,
    table_id=settings.bq_table_id,
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Liveness/readiness probe for Cloud Run"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": settings.gcp_project
    }


@app.post("/", status_code=status.HTTP_200_OK)
async def handle_cloudevent(request: Request):
    """
    Handles incoming CloudEvent HTTP POST requests from Eventarc
    (specifically google.cloud.storage.object.v1.finalized events).
    """
    # 1. Parse CloudEvent from HTTP request
    try:
        headers = dict(request.headers)
        body = await request.body()
        event = from_http(headers, body)
    except Exception as e:
        logger.error(f"Failed to parse CloudEvent headers or body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CloudEvent: {str(e)}"
        )

    event_type = event.get("type", "")
    logger.info(f"Received CloudEvent ID: {event.get('id')} Type: {event_type}")

    # Check for expected GCS object finalized event type or generic pubsub message
    data = event.data
    if not isinstance(data, dict):
        logger.error(f"Event data payload is not a valid JSON dict: {data}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CloudEvent data must be a JSON object"
        )

    try:
        storage_data = StorageObjectData.model_validate(data)
    except Exception as e:
        logger.error(f"Invalid StorageObjectData format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payload does not match GCS object schema: {str(e)}"
        )

    bucket_name = storage_data.bucket
    object_name = storage_data.name

    logger.info(f"Processing object gs://{bucket_name}/{object_name}")

    # Ignore directory marker objects
    if object_name.endswith("/"):
        logger.info(f"Skipping folder marker: {object_name}")
        return JSONResponse(content={"message": "Skipped folder marker"})

    # 2. Download object from Cloud Storage
    try:
        file_bytes = gcs_helper.download_file_bytes(bucket_name, object_name)
    except Exception as e:
        logger.error(f"Error downloading gs://{bucket_name}/{object_name}: {e}")
        # Return 500 so Pub/Sub/Eventarc retries temporary network failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve file from GCS: {str(e)}"
        )

    # 3. Process document (Extract text & tags, simulate OCR when needed)
    try:
        extraction = process_document(
            filename=object_name,
            content_type=storage_data.contentType,
            file_bytes=file_bytes
        )
    except Exception as e:
        logger.error(f"Failed processing document {object_name}: {e}. Moving to quarantine.")
        try:
            gcs_helper.move_to_quarantine(bucket_name, object_name, settings.dlq_bucket_name)
        except Exception as dlq_err:
            logger.error(f"Failed moving {object_name} to quarantine: {dlq_err}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Document processing failed, moved to quarantine DLQ", "error": str(e)}
        )

    # 4. Construct BigQuery Record
    doc_id = storage_data.generation or str(uuid.uuid4())
    upload_time = storage_data.timeCreated or datetime.now(timezone.utc)
    processed_time = datetime.now(timezone.utc)
    size_bytes = int(storage_data.size) if storage_data.size and storage_data.size.isdigit() else len(file_bytes)

    metadata_record = DocumentMetadataRecord(
        document_id=doc_id,
        bucket_name=bucket_name,
        file_name=object_name,
        content_type=storage_data.contentType,
        size_bytes=size_bytes,
        upload_timestamp=upload_time,
        processed_timestamp=processed_time,
        word_count=extraction.word_count,
        tags=extraction.tags,
        ocr_simulated=extraction.ocr_simulated,
        status="SUCCESS"
    )

    # 5. Stream record to BigQuery
    try:
        bq_writer.insert_record(metadata_record)
    except Exception as e:
        logger.error(f"Failed to stream metadata to BigQuery for {object_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream record to BigQuery: {str(e)}"
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "document_id": doc_id,
            "file_name": object_name,
            "word_count": extraction.word_count,
            "tags": extraction.tags,
            "ocr_simulated": extraction.ocr_simulated
        }
    )
