from __future__ import annotations
import logging
from typing import Optional
from google.cloud import storage

logger = logging.getLogger(__name__)


class GCSHelper:
    def __init__(self, client: storage.Client | None = None):
        self._client = client

    @property
    def client(self) -> storage.Client:
        if self._client is None:
            self._client = storage.Client()
        return self._client

    def download_file_bytes(self, bucket_name: str, blob_name: str) -> bytes:
        """Downloads document bytes from GCS bucket."""
        logger.info(f"Downloading gs://{bucket_name}/{blob_name}")
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()

    def move_to_quarantine(self, source_bucket_name: str, blob_name: str, dlq_bucket_name: str) -> None:
        """Moves corrupted / failed files to quarantine DLQ bucket."""
        logger.warning(f"Quarantining gs://{source_bucket_name}/{blob_name} to gs://{dlq_bucket_name}/{blob_name}")
        source_bucket = self.client.bucket(source_bucket_name)
        source_blob = source_bucket.blob(blob_name)
        dest_bucket = self.client.bucket(dlq_bucket_name)
        source_bucket.copy_blob(source_blob, dest_bucket, blob_name)
        source_blob.delete()
