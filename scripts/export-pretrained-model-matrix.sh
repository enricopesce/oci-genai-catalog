#!/usr/bin/env bash
# Export OCI Generative AI pretrained model availability and dedicated-unit limits.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/export-pretrained-model-matrix.sh --compartment-id OCID [options]

Export the OCI Generative AI model collection and dedicated-unit service limits
for every active region subscribed to the configured tenancy. Regions without
the service or access are recorded in "failures"; the export still completes.

Options:
  --compartment-id OCID  Compartment OCID used by OCI Generative AI (required)
  --profile NAME         OCI CLI profile (default: DEFAULT)
  --auth METHOD          OCI CLI auth method, e.g. security_token
  --tenancy-id OCID      Tenancy OCID (read from the OCI CLI profile by default)
  --regions LIST         Comma-separated explicit regions instead of subscribed regions
  --parallel COUNT       Maximum concurrent region queries (default: 6)
  --output PATH          Destination JSON (default: pretrained-model-matrix.json)
  --catalog-output PATH  Write a CLI-only pretrained-inventory snapshot to PATH
  -h, --help             Show this help
EOF
}

compartment_id=''
profile='DEFAULT'
auth=''
tenancy_id=''
regions_csv=''
parallel=6
output='pretrained-model-matrix.json'
catalog_output=''

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compartment-id) compartment_id=${2:?missing value for --compartment-id}; shift 2 ;;
    --profile) profile=${2:?missing value for --profile}; shift 2 ;;
    --auth) auth=${2:?missing value for --auth}; shift 2 ;;
    --tenancy-id) tenancy_id=${2:?missing value for --tenancy-id}; shift 2 ;;
    --regions) regions_csv=${2:?missing value for --regions}; shift 2 ;;
    --parallel) parallel=${2:?missing value for --parallel}; shift 2 ;;
    --output) output=${2:?missing value for --output}; shift 2 ;;
    --catalog-output) catalog_output=${2:?missing value for --catalog-output}; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! "$parallel" =~ ^[1-9][0-9]*$ ]]; then
  printf '%s\n' '--parallel must be a positive integer.' >&2
  exit 2
fi

if [[ -z "$compartment_id" ]]; then
  printf '%s\n' '--compartment-id is required.' >&2
  usage >&2
  exit 2
fi

command -v oci >/dev/null || { printf '%s\n' 'OCI CLI (oci) is required.' >&2; exit 1; }
command -v jq >/dev/null || { printf '%s\n' 'jq is required.' >&2; exit 1; }

oci_auth=(--profile "$profile")
if [[ -n "$auth" ]]; then
  oci_auth+=(--auth "$auth")
fi

if [[ -z "$tenancy_id" ]]; then
  config_file=${OCI_CLI_CONFIG_FILE:-${HOME:?}/.oci/config}
  if [[ -r "$config_file" ]]; then
    tenancy_id=$(awk -F= -v section="[$profile]" '
      $0 == section {in_section = 1; next}
      /^\[/ {in_section = 0}
      in_section {
        key = $1
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", key)
        if (key == "tenancy") {
          sub(/^[^=]*=[[:space:]]*/, "")
          sub(/[[:space:]]+$/, "")
          print
          exit
        }
      }
    ' "$config_file")
  fi
fi
if [[ -z "$tenancy_id" ]]; then
  printf '%s\n' 'Unable to determine tenancy OCID. Supply --tenancy-id explicitly.' >&2
  exit 1
fi

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
successes="$tmp_dir/successes.jsonl"
cluster_successes="$tmp_dir/cluster-successes.jsonl"
failures="$tmp_dir/failures.jsonl"
success_dir="$tmp_dir/successes"
cluster_success_dir="$tmp_dir/cluster-successes"
failure_dir="$tmp_dir/failures"
mkdir -p "$success_dir" "$cluster_success_dir" "$failure_dir"
: > "$successes"
: > "$cluster_successes"
: > "$failures"

region_discovery='explicit region list'
if [[ -n "$regions_csv" ]]; then
  IFS=',' read -r -a regions <<< "$regions_csv"
else
  regions_json="$tmp_dir/region-subscriptions.json"
  oci iam region-subscription list \
    "${oci_auth[@]}" \
    --tenancy-id "$tenancy_id" \
    --output json > "$regions_json"
  mapfile -t regions < <(
    jq -r '(.data // .items // [])[]
      | select(.status == "READY")
      | (."region-name" // .regionName // ."region-key" // .regionKey)' "$regions_json" | sort -u
  )
  region_discovery='active OCI region subscriptions (READY)'
fi

if [[ ${#regions[@]} -eq 0 ]]; then
  printf '%s\n' 'No active regions were discovered. Use --regions to provide a list explicitly.' >&2
  exit 1
fi

fetch_region() {
  local region=$1
  local response="$tmp_dir/$region.json"
  printf 'Fetching %s...\n' "$region" >&2
  if oci generative-ai model-collection list-models \
      "${oci_auth[@]}" \
      --region "$region" \
      --compartment-id "$compartment_id" \
      --all \
      --no-retry \
      --output json > "$response" 2> "$tmp_dir/$region.err"; then
    jq -c --arg region "$region" '
      (.data.items // .items // []) as $items
      | {region: $region, modelCount: ($items | length), items: $items}
    ' "$response" > "$success_dir/$region.json"
  else
    jq -cn --arg region "$region" --rawfile error "$tmp_dir/$region.err" \
      '{region: $region, query: "models", error: ($error | rtrimstr("\n"))}' \
      > "$failure_dir/$region-models.json"
  fi

  local limits_response="$tmp_dir/$region-limits.json"
  if oci limits value list \
      "${oci_auth[@]}" \
      --region "$region" \
      --compartment-id "$tenancy_id" \
      --service-name ai-generative \
      --all \
      --no-retry \
      --output json > "$limits_response" 2> "$tmp_dir/$region-limits.err"; then
    jq -c --arg region "$region" '
      [(.data // [])[] | select(.name | startswith("dedicated-unit-"))] as $items
      | {region: $region, limitCount: ($items | length), items: $items}
    ' "$limits_response" > "$cluster_success_dir/$region.json"
  else
    jq -cn --arg region "$region" --rawfile error "$tmp_dir/$region-limits.err" \
      '{region: $region, query: "clusterSizing", error: ($error | rtrimstr("\n"))}' \
      > "$failure_dir/$region-cluster-sizing.json"
  fi
}

running=0
for region in "${regions[@]}"; do
  fetch_region "$region" &
  ((running += 1))
  if ((running >= parallel)); then
    wait -n || true
    running=$((running - 1))
  fi
done
wait || true

for region in "${regions[@]}"; do
  if [[ -f "$success_dir/$region.json" ]]; then
    cat "$success_dir/$region.json" >> "$successes"
  fi
  if [[ -f "$cluster_success_dir/$region.json" ]]; then
    cat "$cluster_success_dir/$region.json" >> "$cluster_successes"
  fi
  if [[ -f "$failure_dir/$region-models.json" ]]; then
    cat "$failure_dir/$region-models.json" >> "$failures"
  fi
  if [[ -f "$failure_dir/$region-cluster-sizing.json" ]]; then
    cat "$failure_dir/$region-cluster-sizing.json" >> "$failures"
  fi
done

regions_object="$tmp_dir/regions.json"
cluster_sizing_object="$tmp_dir/cluster-sizing.json"
failures_array="$tmp_dir/failures.json"
jq -s 'map({key: .region, value: {modelCount: .modelCount, items: .items}}) | from_entries' \
  "$successes" > "$regions_object"
jq -s 'map({key: .region, value: {limitCount: .limitCount, items: .items}}) | from_entries' \
  "$cluster_successes" > "$cluster_sizing_object"
jq -s '.' "$failures" > "$failures_array"

jq -n \
  --arg generated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg profile "$profile" \
  --arg region_discovery "$region_discovery" \
  --slurpfile regions "$regions_object" \
  --slurpfile cluster_sizing "$cluster_sizing_object" \
  --slurpfile failures "$failures_array" \
  '{
    metadata: {
      generatedAt: $generated_at,
      sources: [
        "OCI CLI generative-ai model-collection list-models",
        "OCI CLI limits value list --service-name ai-generative"
      ],
      profile: $profile,
      scope: "active OCI regions queryable by the configured profile",
      regionDiscovery: $region_discovery
    },
    regions: $regions[0],
    clusterSizingByRegion: $cluster_sizing[0],
    failures: $failures[0]
  }' > "$output"

if [[ -n "$catalog_output" ]]; then
  jq '
    def model_records:
      [.regions | to_entries[] | .key as $region | .value.items[] | . + {__region: $region}]
      | sort_by(."display-name" // .displayName)
      | group_by(."display-name" // .displayName)
      | map(
          . as $entries
          | $entries[0] as $first
          | {
              name: ($first["display-name"] // $first.displayName),
              id: ($first["display-name"] // $first.displayName),
              provider: $first.vendor,
              capabilities: ([$entries[].capabilities[]?] | unique | sort),
              type: $first.type,
              isLongTermSupported: ([$entries[] | (."is-long-term-supported" // .isLongTermSupported // false)] | all),
              isImageTextToTextSupported: ([$entries[].capabilities[]?] | index("IMAGE_TEXT_TO_TEXT") != null),
              regionalInventory: (
                reduce $entries[] as $entry ({};
                  .[$entry.__region] = {
                    lifecycleState: ($entry["lifecycle-state"] // $entry.lifecycleState),
                    lifecycleDetails: ($entry["lifecycle-details"] // $entry.lifecycleDetails),
                    timeCreated: ($entry["time-created"] // $entry.timeCreated),
                    timeDeprecated: ($entry["time-deprecated"] // $entry.timeDeprecated),
                    timeOnDemandRetired: ($entry["time-on-demand-retired"] // $entry.timeOnDemandRetired),
                    timeDedicatedRetired: ($entry["time-dedicated-retired"] // $entry.timeDedicatedRetired)
                  }
                )
              )
            }
        );
    model_records as $all
    | {
        metadata: {
          generatedAt: .metadata.generatedAt,
          sources: .metadata.sources,
          scope: .metadata.scope,
          limitations: [
            "CLI output is the sole source for this snapshot.",
            "OCI CLI does not expose context windows, model tiers, use-case descriptions, or a definitive per-region on-demand access mode.",
            "regionalInventory records observed lifecycle; it must not be treated as catalog.json pretrained regions access map.",
            "clusterSizingByRegion contains tenancy service-limit names and values, not model-to-shape compatibility or proof that capacity is available."
          ],
          successfulRegions: (.regions | keys | sort),
          failedRegions: ([.failures[].region] | unique | sort),
          failedQueries: [.failures[] | {region, query}]
        },
        clusterSizingByRegion: .clusterSizingByRegion,
        chatModels: [$all[] | select(.capabilities | index("CHAT"))],
        embeddingModels: [$all[] | select(.capabilities | index("TEXT_EMBEDDINGS"))],
        rerankModels: [$all[] | select(.capabilities | index("TEXT_RERANK"))],
        otherModels: [$all[] | select(
          (.capabilities | index("CHAT") | not)
          and (.capabilities | index("TEXT_EMBEDDINGS") | not)
          and (.capabilities | index("TEXT_RERANK") | not)
        )]
      }
  ' "$output" > "$catalog_output"
  printf 'Wrote CLI-only catalog snapshot to %s\n' "$catalog_output"
fi

printf 'Wrote %s model region(s), %s sizing region(s), and %s failed query(s) to %s\n' \
  "$(jq -s 'length' "$successes")" \
  "$(jq -s 'length' "$cluster_successes")" \
  "$(jq -s 'length' "$failures")" \
  "$output"
