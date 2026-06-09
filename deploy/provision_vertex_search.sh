#!/usr/bin/env bash
# Provision the Vertex AI Search (Discovery Engine) data store that grounds the
# research sub-agent, and import the canonical taxonomy corpus into it.
#
# Idempotent. If anything here fails, the agent still works on the bundled
# local-corpus fallback (see concierge/grounding.py) — grounding never hard-fails.
#
# After this runs, set on the concierge Cloud Run service:
#   VERTEX_SEARCH_DATASTORE=<DATASTORE>   VERTEX_SEARCH_LOCATION=global
set -euo pipefail

PROJECT="${PROJECT:-tools-cashtimepay-com}"
LOCATION="${VERTEX_SEARCH_LOCATION:-global}"
DATASTORE="${DATASTORE:-cashtime-taxonomy}"
BUCKET="${BUCKET:-gs://${PROJECT}-concierge-grounding}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORPUS="${ROOT}/concierge/data/taxonomy_corpus.json"
JSONL="/tmp/taxonomy_corpus.jsonl"
API="https://discoveryengine.googleapis.com/v1"

log() { printf '\033[1;34m[vertex]\033[0m %s\n' "$*"; }

# 1) corpus.json → Discovery Engine JSONL (id + structData per line).
python3 - "$CORPUS" "$JSONL" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
docs = json.load(open(src))["documents"]
with open(dst, "w") as f:
    for d in docs:
        struct = {
            "enum": d["enum"], "type": d["type"], "title": d["title"],
            "text": d.get("text", ""),
            "keywords": " ".join(d.get("keywords", [])),
            "sub_niches": " ".join(d.get("sub_niches", [])),
        }
        f.write(json.dumps({"id": d["id"], "structData": struct}) + "\n")
print(f"wrote {len(docs)} docs -> {dst}")
PY

# 2) upload corpus to GCS.
log "Uploading corpus to ${BUCKET}…"
gsutil mb -p "${PROJECT}" -l europe-west6 "${BUCKET}" 2>/dev/null || true
gsutil cp "${JSONL}" "${BUCKET}/taxonomy_corpus.jsonl"

TOKEN="$(gcloud auth print-access-token)"
PARENT="projects/${PROJECT}/locations/${LOCATION}/collections/default_collection"

# 3) create the data store (structured content) if missing.
if ! curl -sf -H "Authorization: Bearer ${TOKEN}" \
      "${API}/${PARENT}/dataStores/${DATASTORE}" >/dev/null 2>&1; then
  log "Creating data store '${DATASTORE}'…"
  curl -s -X POST \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: ${PROJECT}" \
    "${API}/${PARENT}/dataStores?dataStoreId=${DATASTORE}" \
    -d '{
      "displayName": "CashTime canonical taxonomy",
      "industryVertical": "GENERIC",
      "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
      "contentConfig": "NO_CONTENT"
    }' | python3 -c "import sys,json;print(json.load(sys.stdin).get('name','(op submitted)'))" || true
  sleep 10
else
  log "Data store '${DATASTORE}' already exists."
fi

# 4) import the documents from GCS.
log "Importing taxonomy documents…"
curl -s -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT}" \
  "${API}/${PARENT}/dataStores/${DATASTORE}/branches/default_branch/documents:import" \
  -d "{
    \"gcsSource\": {\"inputUris\": [\"${BUCKET}/taxonomy_corpus.jsonl\"], \"dataSchema\": \"document\"},
    \"reconciliationMode\": \"FULL\"
  }" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('name','(import op submitted)'))" || true

log "Done. Set VERTEX_SEARCH_DATASTORE=${DATASTORE} on the concierge service to enable the live grounding backend."
