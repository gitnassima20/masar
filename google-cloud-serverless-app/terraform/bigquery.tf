resource "google_bigquery_dataset" "pipeline_dataset" {
  dataset_id  = var.bq_dataset_id
  location    = var.region
  description = "Dataset storing extracted document metadata"

  depends_on = [google_project_service.enabled_services]
}

resource "google_bigquery_table" "metadata_table" {
  dataset_id = google_bigquery_dataset.pipeline_dataset.dataset_id
  table_id   = var.bq_table_id

  time_partitioning {
    type  = "DAY"
    field = "upload_timestamp"
  }

  clustering = ["status", "ocr_simulated"]

  schema = jsonencode([
    {
      name        = "document_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Unique ID / GCS generation identifier"
    },
    {
      name        = "bucket_name"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Source GCS bucket"
    },
    {
      name        = "file_name"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "GCS object path"
    },
    {
      name        = "content_type"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "MIME type"
    },
    {
      name        = "size_bytes"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "File size in bytes"
    },
    {
      name        = "upload_timestamp"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Timestamp when file was uploaded"
    },
    {
      name        = "processed_timestamp"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Timestamp when file was processed"
    },
    {
      name        = "word_count"
      type        = "INT64"
      mode        = "REQUIRED"
      description = "Extracted word count"
    },
    {
      name        = "tags"
      type        = "STRING"
      mode        = "REPEATED"
      description = "Extracted keyword tags"
    },
    {
      name        = "ocr_simulated"
      type        = "BOOLEAN"
      mode        = "REQUIRED"
      description = "Whether simulated OCR fallback was used"
    },
    {
      name        = "status"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Processing status"
    }
  ])
}

# Grant BigQuery data editor and write permissions to Processor SA
resource "google_project_iam_member" "processor_bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.processor_sa.email}"
}

resource "google_project_iam_member" "processor_bq_storage_write" {
  project = var.project_id
  role    = "roles/bigquery.storageWriteApiUser"
  member  = "serviceAccount:${google_service_account.processor_sa.email}"
}
