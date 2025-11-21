provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "The ID of the Google Cloud project"
}

variable "region" {
  description = "The region to deploy resources to"
  default     = "us-central1"
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "shop-agent-repo"
  description   = "Docker repository for Shop Agent"
  format        = "DOCKER"
}

# Cloud Run Service (Backend)
resource "google_cloud_run_service" "backend" {
  name     = "shop-agent-backend"
  location = var.region

  template {
    spec {
      containers {
        image = "us-docker.pkg.dev/cloudrun/container/hello" # Placeholder until built
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Allow unauthenticated access to backend
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# GCS Bucket for Widget
resource "google_storage_bucket" "widget_bucket" {
  name          = "${var.project_id}-shop-agent-widget"
  location      = var.region
  force_destroy = true

  website {
    main_page_suffix = "index.html"
  }
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Make bucket public
resource "google_storage_bucket_iam_member" "public_bucket" {
  bucket = google_storage_bucket.widget_bucket.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
