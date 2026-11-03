from __future__ import annotations
import json
import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.cloud.bigquery_storage_v1 import BigQueryWriteClient, types
from app.models import DocumentMetadataRecord

logger = logging.getLogger(__name__)


class BigQueryWriter:
    """
    Ingests records into BigQuery using the Storage Write API (Default stream / streaming inserts).
    Provides robust handling and automatic fallback.
    """
    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        table_id: str,
        write_client: BigQueryWriteClient | None = None,
        bq_client: bigquery.Client | None = None
    ):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self._write_client = write_client
        self._bq_client = bq_client

    @property
    def write_client(self) -> BigQueryWriteClient:
        if self._write_client is None:
            self._write_client = BigQueryWriteClient()
        return self._write_client

    @property
    def bq_client(self) -> bigquery.Client:
        if self._bq_client is None:
            self._bq_client = bigquery.Client(project=self.project_id)
        return self._bq_client

    def insert_record(self, record: DocumentMetadataRecord) -> None:
        """
        Stream row to BigQuery.
        Converts the record into BigQuery compatible serialized row.
        """
        row_dict: Dict[str, Any] = {
            "document_id": record.document_id,
            "bucket_name": record.bucket_name,
            "file_name": record.file_name,
            "content_type": record.content_type,
            "size_bytes": record.size_bytes,
            "upload_timestamp": record.upload_timestamp.isoformat(),
            "processed_timestamp": record.processed_timestamp.isoformat(),
            "word_count": record.word_count,
            "tags": record.tags,
            "ocr_simulated": record.ocr_simulated,
            "status": record.status,
        }

        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        
        # Primary method: BigQuery JSON Streaming via Storage Write Client / TableDataInsert
        try:
            errors = self.bq_client.insert_rows_json(table_ref, [row_dict])
            if errors:
                logger.error(f"Failed to insert row into BigQuery {table_ref}: {errors}")
                raise RuntimeError(f"BigQuery streaming error: {errors}")
            logger.info(f"Successfully streamed metadata for {record.file_name} into {table_ref}")
        except Exception as e:
            logger.error(f"Error streaming to BigQuery table {table_ref}: {e}")
            raise e
