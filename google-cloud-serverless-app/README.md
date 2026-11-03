# Serverless Event-Driven Document Processing Pipeline on Google Cloud

A complete event-driven pipeline on Google Cloud Platform (GCP) that listens for file uploads in Cloud Storage, triggers a Python FastAPI service on Cloud Run via Eventarc, extracts metadata and text (with simulated OCR fallback for binary/scanned files), and streams records into BigQuery using the Storage Write API.

---

## Architecture

```
User -> GCS Bucket -> Eventarc (GCS Object Finalized) -> Cloud Run (FastAPI) -> BigQuery (Storage Write API)
                                                                 │
                                                                 └── (On failure/corrupted) ──> DLQ GCS Bucket & Topic
```

---

## Repository Structure

```
.
├── terraform/                # Infrastructure as Code
│   ├── main.tf               # Provider & required Google APIs
│   ├── variables.tf          # Configurable variables (project, region, buckets)
│   ├── gcs.tf                # Storage buckets (raw + DLQ) & IAM
│   ├── bigquery.tf           # BigQuery dataset, partitioned table, IAM
│   ├── cloud_run.tf          # Cloud Run service & invoker permissions
│   ├── eventarc.tf           # Eventarc trigger & Pub/Sub DLQ topic
│   └── outputs.tf            # Deployment outputs
├── src/                      # Python FastAPI application
│   ├── app/
│   │   ├── config.py         # App configuration via pydantic-settings
│   │   ├── models.py         # CloudEvent and BigQuery data models
│   │   ├── extractor.py      # PDF / text extractor & mock OCR engine
│   │   ├── gcs_client.py     # Cloud Storage helper
│   │   ├── bq_writer.py      # BigQuery streaming write client
│   │   └── main.py           # FastAPI entrypoint & CloudEvent route
│   ├── tests/                # Test suite
│   │   ├── test_api.py       # CloudEvent HTTP handler tests
│   │   └── test_extractor.py # Document parsing & OCR unit tests
│   ├── Dockerfile            # Container configuration
│   └── requirements.txt      # Python dependencies
├── samples/
│   └── sample_cloudevent.json# Example Eventarc payload for local testing
├── docker-compose.yml        # Local container runner
└── README.md
```

---

## Getting Started

### 1. Local Testing

#### Run unit tests with pytest:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r src/requirements.txt
PYTHONPATH=src pytest src/tests
```

#### Run locally with Docker Compose:
```bash
docker compose up --build
```

#### Test CloudEvent delivery locally:
```bash
curl -X POST http://localhost:8080/ \
  -H "ce-id: local-test-01" \
  -H "ce-source: //storage.googleapis.com/projects/_/buckets/my-bucket" \
  -H "ce-specversion: 1.0" \
  -H "ce-type: google.cloud.storage.object.v1.finalized" \
  -H "Content-Type: application/json" \
  -d @samples/sample_cloudevent.json
```

---

## 2. Infrastructure Deployment (Terraform)

### Prerequisites
- Google Cloud CLI (`gcloud`) installed and logged in: `gcloud auth application-default login`
- Terraform >= 1.5.0

### Step 1: Build & Push Container to Artifact Registry
```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export REPO_NAME="doc-pipeline"
export IMAGE_NAME="document-processor"

# Create Artifact Registry repo (if not already existing)
gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$REGION \
  --project=$PROJECT_ID

# Build and push the image via Cloud Build
gcloud builds submit src/ \
  --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
  --project=$PROJECT_ID
```

### Step 2: Deploy Terraform
```bash
cd terraform

terraform init

terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="container_image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
```

---

## 3. Verifying the Pipeline
Upload a file to the created raw documents bucket:
```bash
gsutil cp samples/sample_contract.txt gs://<raw_documents_bucket_name>/contracts/sample_contract.txt
```
Check BigQuery for the ingested record:
```sql
SELECT * FROM `<project_id>.document_processing.document_metadata`
ORDER BY processed_timestamp DESC
LIMIT 10;
```
