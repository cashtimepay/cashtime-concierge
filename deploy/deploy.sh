#!/usr/bin/env bash
# CashTime Brand Concierge — one-shot deploy to Cloud Run + Vertex AI Search.
#
# Idempotent. Safe to re-run. Targets project tools-cashtimepay-com / europe-west6.
#
# Usage:
#   ./deploy/deploy.sh preflight     # checks auth/project/APIs, creates nothing
#   ./deploy/deploy.sh infra         # APIs + Artifact Registry + SA + secrets + Vertex index
#   ./deploy/deploy.sh api           # build + deploy the concierge service
#   ./deploy/deploy.sh ui            # build + deploy the Brand UI
#   ./deploy/deploy.sh all           # infra + api + ui
#
# Secrets must be populated in Secret Manager before `api` (see `infra` output).
set -euo pipefail

PROJECT="${PROJECT:-tools-cashtimepay-com}"
REGION="${REGION:-europe-west6}"
REPO="${REPO:-cashtime}"
SA_NAME="cashtime-concierge"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
DATASTORE="${DATASTORE:-cashtime-taxonomy}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() { printf '\033[1;34m[deploy]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[deploy]\033[0m %s\n' "$*"; }

preflight() {
  log "Active account: $(gcloud config get-value account 2>/dev/null)"
  log "Target project: ${PROJECT}  region: ${REGION}"
  if ! gcloud projects describe "${PROJECT}" >/dev/null 2>&1; then
    warn "Cannot describe project ${PROJECT}. Run: gcloud auth login (dmitry@cashtimepay.com) and ensure access."
    return 1
  fi
  log "Project reachable. Enabled run/build APIs:"
  gcloud services list --enabled --project "${PROJECT}" \
    --filter="config.name:(run.googleapis.com OR cloudbuild.googleapis.com OR discoveryengine.googleapis.com OR artifactregistry.googleapis.com)" \
    --format="value(config.name)" || true
  log "Preflight OK."
}

infra() {
  log "Enabling APIs…"
  gcloud services enable \
    run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
    secretmanager.googleapis.com discoveryengine.googleapis.com iap.googleapis.com \
    aiplatform.googleapis.com cloudtrace.googleapis.com \
    --project "${PROJECT}"

  log "Artifact Registry repo '${REPO}'…"
  gcloud artifacts repositories describe "${REPO}" --location "${REGION}" --project "${PROJECT}" >/dev/null 2>&1 || \
    gcloud artifacts repositories create "${REPO}" --repository-format=docker \
      --location "${REGION}" --project "${PROJECT}" --description "CashTime images"

  log "Service account '${SA_EMAIL}'…"
  gcloud iam service-accounts describe "${SA_EMAIL}" --project "${PROJECT}" >/dev/null 2>&1 || \
    gcloud iam service-accounts create "${SA_NAME}" --project "${PROJECT}" \
      --display-name "CashTime Brand Concierge runtime"
  for role in roles/aiplatform.user roles/discoveryengine.viewer \
              roles/cloudtrace.agent roles/secretmanager.secretAccessor; do
    gcloud projects add-iam-policy-binding "${PROJECT}" \
      --member "serviceAccount:${SA_EMAIL}" --role "${role}" --condition=None >/dev/null
  done

  log "Secret Manager placeholders (fill with real values before 'api')…"
  for s in concierge-mcp-bearer concierge-twenty-key concierge-cf-id concierge-cf-secret; do
    gcloud secrets describe "${s}" --project "${PROJECT}" >/dev/null 2>&1 || \
      gcloud secrets create "${s}" --project "${PROJECT}" --replication-policy=automatic
  done
  warn "Populate secrets:  echo -n VALUE | gcloud secrets versions add concierge-twenty-key --data-file=- --project ${PROJECT}"

  log "Provisioning Vertex AI Search index…"
  bash "${ROOT}/deploy/provision_vertex_search.sh" || warn "Vertex index step failed — pipeline still runs on local corpus fallback."
}

api() {
  log "Building + deploying concierge service…"
  gcloud builds submit "${ROOT}" --config "${ROOT}/deploy/cloudbuild.yaml" \
    --project "${PROJECT}" --substitutions "SHORT_SHA=$(git -C "${ROOT}" rev-parse --short HEAD 2>/dev/null || echo manual)"
}

ui() {
  local api_url
  api_url="$(gcloud run services describe cashtime-concierge --region "${REGION}" \
    --project "${PROJECT}" --format='value(status.url)' 2>/dev/null || echo https://concierge-api.cashtimepay.com)"
  log "Building + deploying Brand UI (API=${api_url})…"
  gcloud builds submit "${ROOT}" --config "${ROOT}/deploy/cloudbuild.ui.yaml" \
    --project "${PROJECT}" \
    --substitutions "SHORT_SHA=$(git -C "${ROOT}" rev-parse --short HEAD 2>/dev/null || echo manual),_CONCIERGE_API=${api_url}"
}

case "${1:-preflight}" in
  preflight) preflight ;;
  infra) infra ;;
  api) api ;;
  ui) ui ;;
  all) infra; api; ui ;;
  *) echo "Usage: $0 {preflight|infra|api|ui|all}"; exit 2 ;;
esac
