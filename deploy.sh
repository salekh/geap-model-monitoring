#!/usr/bin/env bash
#
# deploy.sh — Deploy Anthropic model-monitoring dashboards to Google Cloud Monitoring.
#
# Repeatable / idempotent: if a dashboard with the same displayName already
# exists in the project, it is UPDATED in place; otherwise it is created.
# Safe to run as many times as you like.
#
# Usage:
#   ./deploy.sh                     # deploy to the current gcloud project
#   ./deploy.sh -p my-project-id    # deploy to a specific project
#   ./deploy.sh -d dashboards/01-fable5-token-usage.json   # deploy one file only
#   ./deploy.sh --list              # list currently deployed dashboards and exit
#
# Requirements: gcloud (authenticated), python3. Roles: monitoring.editor.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="${SCRIPT_DIR}/dashboards"
PROJECT_ID=""
SINGLE_FILE=""
LIST_ONLY=false

usage() { grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project) PROJECT_ID="$2"; shift 2 ;;
    -d|--dashboard) SINGLE_FILE="$2"; shift 2 ;;
    --list) LIST_ONLY=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

if [[ -z "$PROJECT_ID" ]]; then
  PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
fi
if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: no project set. Use -p PROJECT_ID or 'gcloud config set project'." >&2
  exit 1
fi

echo "Project: ${PROJECT_ID}"

# Fetch existing dashboards once: "displayName<TAB>name" per line.
existing_dashboards() {
  gcloud monitoring dashboards list \
    --project="$PROJECT_ID" \
    --format="value(displayName,name)" 2>/dev/null || true
}

if $LIST_ONLY; then
  echo "Deployed dashboards:"
  existing_dashboards | awk -F'\t' '{printf "  %-55s %s\n", $1, $2}'
  exit 0
fi

# Collect dashboard files to deploy.
declare -a FILES
if [[ -n "$SINGLE_FILE" ]]; then
  [[ -f "$SINGLE_FILE" ]] || { echo "ERROR: file not found: $SINGLE_FILE" >&2; exit 1; }
  FILES=("$SINGLE_FILE")
else
  mapfile -t FILES < <(find "$DASHBOARD_DIR" -maxdepth 1 -name '*.json' | sort)
fi
[[ ${#FILES[@]} -gt 0 ]] || { echo "ERROR: no dashboard JSON files found in ${DASHBOARD_DIR}" >&2; exit 1; }

EXISTING="$(existing_dashboards)"
CREATED=0 UPDATED=0 FAILED=0

for file in "${FILES[@]}"; do
  display_name="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['displayName'])" "$file")"

  # Find an existing dashboard with this exact displayName (first match).
  dash_name="$(printf '%s\n' "$EXISTING" | awk -F'\t' -v dn="$display_name" '$1==dn {print $2; exit}')"

  if [[ -n "$dash_name" ]]; then
    # Update in place. The API requires the current etag for optimistic locking.
    etag="$(gcloud monitoring dashboards describe "$dash_name" --project="$PROJECT_ID" --format='value(etag)')"
    tmp="$(mktemp)"
    python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
d['name'] = sys.argv[2]
d['etag'] = sys.argv[3]
json.dump(d, open(sys.argv[4], 'w'))
" "$file" "$dash_name" "$etag" "$tmp"
    if gcloud monitoring dashboards update "$dash_name" \
         --project="$PROJECT_ID" --config-from-file="$tmp" >/dev/null 2>&1; then
      echo "UPDATED  ${display_name}"
      UPDATED=$((UPDATED+1))
    else
      echo "FAILED   ${display_name} (update)" >&2
      FAILED=$((FAILED+1))
    fi
    rm -f "$tmp"
  else
    if out="$(gcloud monitoring dashboards create \
         --project="$PROJECT_ID" --config-from-file="$file" --format='value(name)' 2>&1)"; then
      echo "CREATED  ${display_name}"
      CREATED=$((CREATED+1))
    else
      echo "FAILED   ${display_name}: ${out}" >&2
      FAILED=$((FAILED+1))
    fi
  fi
done

echo
echo "Done. created=${CREATED} updated=${UPDATED} failed=${FAILED}"
echo "View: https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
[[ $FAILED -eq 0 ]]
