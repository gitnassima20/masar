output "raw_documents_bucket" {
  description = "GCS bucket for uploading raw documents"
  value       = google_storage_bucket.raw_documents.name
}

output "dlq_bucket" {
  description = "Quarantine / DLQ GCS bucket"
  value       = google_storage_bucket.dlq_bucket.name
}

output "cloud_run_service_uri" {
  description = "URI of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.processor_service.uri
}

output "bigquery_table" {
  description = "Full ID of the BigQuery destination table"
  value       = "${var.project_id}.${google_bigquery_dataset.pipeline_dataset.dataset_id}.${google_bigquery_table.metadata_table.table_id}"
}

output "eventarc_trigger_name" {
  description = "Name of the Eventarc trigger"
  value       = google_eventarc_trigger.gcs_finalize_trigger.name
}
