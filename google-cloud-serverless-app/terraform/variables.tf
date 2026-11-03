variable "project_id" {
  description = "The GCP project ID to deploy resources into"
  type        = string
}

variable "region" {
  description = "The GCP region for regional resources"
  type        = string
  default     = "us-central1"
}

variable "raw_documents_bucket_name" {
  description = "Name for the raw document ingestion GCS bucket"
  type        = string
  default     = "doc-pipeline-raw-documents"
}

variable "dlq_bucket_name" {
  description = "Name for the dead-letter / quarantine GCS bucket"
  type        = string
  default     = "doc-pipeline-quarantine-dlq"
}

variable "bq_dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
  default     = "document_processing"
}

variable "bq_table_id" {
  description = "BigQuery table ID"
  type        = string
  default     = "document_metadata"
}

variable "container_image" {
  description = "Container image URL for the Cloud Run service"
  type        = string
  default     = "gcr.io/cloudrun/hello" # Set your Artifact Registry image URL here
}
