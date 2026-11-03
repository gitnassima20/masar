from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StorageObjectData(BaseModel):
    """CloudEvent payload schema for google.cloud.storage.object.v1.finalized"""
    bucket: str
    name: str
    metageneration: Optional[str] = None
    contentType: Optional[str] = Field(default=None, alias="contentType")
    size: Optional[str] = None
    timeCreated: Optional[datetime] = None
    updated: Optional[datetime] = None
    generation: Optional[str] = None


class ExtractionResult(BaseModel):
    """Result of document extraction and simulated OCR"""
    text: str
    word_count: int
    tags: List[str]
    ocr_simulated: bool


class DocumentMetadataRecord(BaseModel):
    """BigQuery row schema"""
    document_id: str
    bucket_name: str
    file_name: str
    content_type: Optional[str] = None
    size_bytes: int
    upload_timestamp: datetime
    processed_timestamp: datetime
    word_count: int
    tags: List[str]
    ocr_simulated: bool
    status: str
