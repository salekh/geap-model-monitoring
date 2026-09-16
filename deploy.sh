#!/usr/bin/env bash
#
# deploy.sh — Deploy Anthropic model-monitoring dashboards to Google Cloud Monitoring.
#
# Repeatable / idempotent: if a dashboard with the same displayName already
# exists in the project, it is UPDATED in place; otherwise it is created.
# Safe to run as many times as you like.
#
# Usage:
#   ./deploy.sh                                  # deploy latest (v3.3-final) to active gcloud project
#   ./deploy.sh -c nexus-project                 # deploy using a specific gcloud configuration
#   ./deploy.sh -p my-project-id                 # deploy to a specific project ID
#   ./deploy.sh --version old                    # deploy preserved old version (v2.0-old)
#   ./deploy.sh --version v1.0                   # deploy original baseline version (v1.0-original)
#   ./deploy.sh --both                           # deploy BOTH old ([v2.0 Old] ...) and new (v3.3) side-by-side!
#   ./deploy.sh -d dashboards/01-fable5-token-usage.json   # deploy one file only
#   ./deploy.sh --list                           # list currently deployed dashboards and exit
#   ./deploy.sh --validate                       # run strict mosaic layout & JSON tag validator
#
# Requirements: gcloud (authenticated), python3. Roles: monitoring.editor.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="${SCRIPT_DIR}/dashboards"
PROJECT_ID=""
GCLOUD_CONFIG=""
SINGLE_FILE=""
VERSION_MODE="new"
DEPLOY_BOTH=false
LIST_ONLY=false
VALIDATE_ONLY=false

usage() { grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project) PROJECT_ID="$2"; shift 2 ;;
    -c|--config) GCLOUD_CONFIG="$2"; shift 2 ;;
    -d|--dashboard) SINGLE_FILE="$2"; shift 2 ;;
    -v|--version) VERSION_MODE="$2"; shift 2 ;;
    --both|--side-by-side|--preserve-old-in-cloud) DEPLOY_BOTH=true; shift ;;
    --list) LIST_ONLY=true; shift ;;
    --validate) VALIDATE_ONLY=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

if $VALIDATE_ONLY; then
  python3 "${SCRIPT_DIR}/scripts/validate_dashboards.py" "${DASHBOARD_DIR}"
  exit 0
fi

if [[ -n "$GCLOUD_CONFIG" ]]; then
  export CLOUDSDK_ACTIVE_CONFIG_NAME="$GCLOUD_CONFIG"
  echo "Using gcloud configuration: ${GCLOUD_CONFIG}"
fi

if [[ -z "$PROJECT_ID" ]]; then
  PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
fi
if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: no project set. Use -p PROJECT_ID, -c CONFIG_NAME, or 'gcloud config set project'." >&2
  exit 1
fi

echo "Target GCP Project: ${PROJECT_ID}"

# Fetch existing dashboards once: "displayName<TAB>name" per line.
existing_dashboards() {
  gcloud monitoring dashboards list \
    --project="$PROJECT_ID" \
    --format="value(displayName,name)" 2>/dev/null || true
}

if $LIST_ONLY; then
  echo "Deployed dashboards in ${PROJECT_ID}:"
  existing_dashboards | awk -F'\t' '{printf "  %-60s %s\n", $1, $2}'
  exit 0
fi

resolve_version_dir() {
  local v="$1"
  case "$v" in
    new|v3.3|v3.3-final|final) echo "${DASHBOARD_DIR}" ;;
    old|v2.0|v2.0-old)         echo "${DASHBOARD_DIR}/versions/v2.0-old" ;;
    v1.0|v1.0-original)        echo "${DASHBOARD_DIR}/versions/v1.0-original" ;;
    v3.1|v3.1-iter1|iter1)     echo "${DASHBOARD_DIR}/versions/v3.1-iter1" ;;
    v3.2|v3.2-iter2|iter2)     echo "${DASHBOARD_DIR}/versions/v3.2-iter2" ;;
    *) echo "ERROR: Unknown version '$v'. Supported: new, old, v1.0, v2.0, v3.1, v3.2, v3.3" >&2; exit 1 ;;
  esac
}

EXISTING="$(existing_dashboards)"
CREATED=0 UPDATED=0 FAILED=0

deploy_file_entry() {
  local file="$1"
  local name_prefix="${2:-}"
  local override_version_tag="${3:-}"

  local tmp_src
  tmp_src="$(mktemp)"

  python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
prefix = sys.argv[2]
vtag = sys.argv[3]
if prefix:
    d['displayName'] = prefix + d['displayName']
if vtag:
    if 'labels' not in d or not isinstance(d['labels'], dict):
        d['labels'] = {}
    d['labels']['version'] = vtag
json.dump(d, open(sys.argv[4], 'w'), indent=2)
" "$file" "$name_prefix" "$override_version_tag" "$tmp_src"

  local display_name
  display_name="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['displayName'])" "$tmp_src")"

  # Find an existing dashboard with this exact displayName (first match).
  local dash_name
  dash_name="$(printf '%s\n' "$EXISTING" | awk -F'\t' -v dn="$display_name" '$1==dn {print $2; exit}')"

  if [[ -n "$dash_name" ]]; then
    local etag
    etag="$(gcloud monitoring dashboards describe "$dash_name" --project="$PROJECT_ID" --format='value(etag)')"
    local tmp_upd
    tmp_upd="$(mktemp)"
    python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
d['name'] = sys.argv[2]
d['etag'] = sys.argv[3]
json.dump(d, open(sys.argv[4], 'w'))
" "$tmp_src" "$dash_name" "$etag" "$tmp_upd"
    if gcloud monitoring dashboards update "$dash_name" \
         --project="$PROJECT_ID" --config-from-file="$tmp_upd" >/dev/null 2>&1; then
      echo "UPDATED  ${display_name}"
      UPDATED=$((UPDATED+1))
    else
      echo "FAILED   ${display_name} (update)" >&2
      FAILED=$((FAILED+1))
    fi
    rm -f "$tmp_upd"
  else
    local out
    if out="$(gcloud monitoring dashboards create \
         --project="$PROJECT_ID" --config-from-file="$tmp_src" --format='value(name)' 2>&1)"; then
      echo "CREATED  ${display_name}"
      CREATED=$((CREATED+1))
    else
      echo "FAILED   ${display_name}: ${out}" >&2
      FAILED=$((FAILED+1))
    fi
  fi
  rm -f "$tmp_src"
}

if [[ -n "$SINGLE_FILE" ]]; then
  [[ -f "$SINGLE_FILE" ]] || { echo "ERROR: file not found: $SINGLE_FILE" >&2; exit 1; }
  deploy_file_entry "$SINGLE_FILE" "" ""
elif $DEPLOY_BOTH; then
  echo "Deploying BOTH preserved Old (v2.0-old) and New (v3.3-final) dashboards side-by-side..."
  OLD_DIR="$(resolve_version_dir "old")"
  NEW_DIR="$(resolve_version_dir "new")"
  mapfile -t OLD_FILES < <(find "$OLD_DIR" -maxdepth 1 -name '*.json' | sort)
  mapfile -t NEW_FILES < <(find "$NEW_DIR" -maxdepth 1 -name '*.json' | sort)
  for f in "${OLD_FILES[@]}"; do
    deploy_file_entry "$f" "[v2.0 Old] " "v2-0-old"
  done
  for f in "${NEW_FILES[@]}"; do
    deploy_file_entry "$f" "" "v3-3-final"
  done
else
  TARGET_DIR="$(resolve_version_dir "$VERSION_MODE")"
  echo "Deploying version '${VERSION_MODE}' from ${TARGET_DIR}..."
  mapfile -t FILES < <(find "$TARGET_DIR" -maxdepth 1 -name '*.json' | sort)
  [[ ${#FILES[@]} -gt 0 ]] || { echo "ERROR: no dashboard JSON files found in ${TARGET_DIR}" >&2; exit 1; }
  for f in "${FILES[@]}"; do
    deploy_file_entry "$f" "" ""
  done
fi

echo
echo "Done. created=${CREATED} updated=${UPDATED} failed=${FAILED}"
echo "View in GCP Console: https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
[[ $FAILED -eq 0 ]]
