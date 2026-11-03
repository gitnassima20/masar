# Raw documents ingestion bucket
resource "google_storage_bucket" "raw_documents" {
  name                        = "${var.raw_documents_bucket_name}-${var.project_id}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true

  versioning {
    enabled = true
  }

  depends_on = [google_project_service.enabled_services]
}

# Dead-letter / Quarantine bucket
resource "google_storage_bucket" "dlq_bucket" {
  name                        = "${var.dlq_bucket_name}-${var.project_id}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30 # Retain quarantined items for 30 days
    }
  }

  depends_on = [google_project_service.enabled_services]
}

# Service Account for Cloud Run Processor
resource "google_service_account" "processor_sa" {
  account_id   = "doc-processor-sa"
  display_name = "Cloud Run Document Processor Service Account"
}

# Grant Processor SA permissions on Ingestion bucket
resource "google_storage_bucket_iam_member" "processor_raw_bucket_read" {
  bucket = google_storage_bucket.raw_documents.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.processor_sa.email}"
}

# Grant Processor SA permissions on Quarantine bucket
resource "google_storage_bucket_iam_member" "processor_dlq_bucket_write" {
  bucket = google_storage_bucket.dlq_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.processor_sa.email}"
}

# GCS Pub/Sub Publisher role for Eventarc
data "google_storage_project_service_account" "gcs_account" {
}

resource "google_project_iam_member" "gcs_pubsub_publishing" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}
