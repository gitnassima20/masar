# Service Account for Eventarc Trigger
resource "google_service_account" "eventarc_trigger_sa" {
  account_id   = "eventarc-trigger-sa"
  display_name = "Eventarc Trigger Service Account"
}

# Grant Eventarc SA permission to receive events and invoke Cloud Run
resource "google_project_iam_member" "eventarc_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.eventarc_trigger_sa.email}"
}

# Dead Letter Topic for Eventarc / Pub/Sub
resource "google_pubsub_topic" "eventarc_dlq_topic" {
  name = "doc-processor-dead-letter-topic"
}

# Eventarc Trigger: Listens for GCS Object Finalized events and forwards to Cloud Run
resource "google_eventarc_trigger" "gcs_finalize_trigger" {
  name     = "gcs-doc-upload-trigger"
  location = var.region

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.raw_documents.name
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_v2_service.processor_service.name
      region  = var.region
      path    = "/"
    }
  }

  service_account = google_service_account.eventarc_trigger_sa.email

  depends_on = [
    google_project_iam_member.gcs_pubsub_publishing,
    google_cloud_run_service_iam_member.eventarc_invoker
  ]
}
