# Cloud Run Service for Document Processor
resource "google_cloud_run_v2_service" "processor_service" {
  name     = "document-processor-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER" # Or INGRESS_TRAFFIC_ALL for eventarc invocation

  template {
    service_account = google_service_account.processor_sa.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "BQ_DATASET_ID"
        value = google_bigquery_dataset.pipeline_dataset.dataset_id
      }
      env {
        name  = "BQ_TABLE_ID"
        value = google_bigquery_table.metadata_table.table_id
      }
      env {
        name  = "DLQ_BUCKET_NAME"
        value = google_storage_bucket.dlq_bucket.name
      }
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }

      ports {
        container_port = 8080
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
    }
  }

  depends_on = [
    google_project_service.enabled_services,
    google_bigquery_table.metadata_table
  ]
}

# Allow Eventarc / Pub/Sub to invoke the Cloud Run service
resource "google_cloud_run_service_iam_member" "eventarc_invoker" {
  location = google_cloud_run_v2_service.processor_service.location
  service  = google_cloud_run_v2_service.processor_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.eventarc_trigger_sa.email}"
}
