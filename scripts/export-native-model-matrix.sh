#!/usr/bin/env bash
# Export native OCI Generative AI model availability and dedicated cluster shapes.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/export-native-model-matrix.sh --compartment-id OCID [options]

Export the OCI Generative AI model collection for every public OC1 region that
the configured OCI CLI profile can query. Regions without the service or access
are recorded in "failures"; the export still completes with all successful data.

Options:
  --compartment-id OCID  Compartment OCID used by OCI Generative AI (required)
  --profile NAME         OCI CLI profile (default: DEFAULT)
  --auth METHOD          OCI CLI auth method, e.g. security_token
  --regions LIST         Comma-separated explicit regions instead of all OC1 regions
  --output PATH          Destination JSON (default: native-model-matrix.json)
  --catalog-output PATH  Write a models.json-shaped CLI-only snapshot to PATH
  -h, --help             Show this help
EOF
}

compartment_id=''
profile='DEFAULT'
auth=''
regions_csv=''
output='native-model-matrix.json'
catalog_output=''

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compartment-id) compartment_id=${2:?missing value for --compartment-id}; shift 2 ;;
    --profile) profile=${2:?missing value for --profile}; shift 2 ;;
    --auth) auth=${2:?missing value for --auth}; shift 2 ;;
    --regions) regions_csv=${2:?missing value for --regions}; shift 2 ;;
    --output) output=${2:?missing value for --output}; shift 2 ;;
    --catalog-output) catalog_output=${2:?missing value for --catalog-output}; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

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

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
successes="$tmp_dir/successes.jsonl"
failures="$tmp_dir/failures.jsonl"
: > "$successes"
: > "$failures"

if [[ -n "$regions_csv" ]]; then
  IFS=',' read -r -a regions <<< "$regions_csv"
else
  regions_json="$tmp_dir/regions.json"
  oci iam region list "${oci_auth[@]}" --output json > "$regions_json"
  mapfile -t regions < <(
    jq -r '(.data // .items // [])[]
      | select((."realm-key" // .realmKey) == "oc1")
      | (.key // .name)' "$regions_json" | sort -u
  )
fi

if [[ ${#regions[@]} -eq 0 ]]; then
  printf '%s\n' 'No OC1 regions were discovered. Use --regions to provide a list explicitly.' >&2
  exit 1
fi

for region in "${regions[@]}"; do
  response="$tmp_dir/$region.json"
  printf 'Fetching %s...\n' "$region" >&2
  if oci generative-ai model-collection list-models \
      "${oci_auth[@]}" \
      --region "$region" \
      --compartment-id "$compartment_id" \
      --all \
      --output json > "$response" 2> "$tmp_dir/$region.err"; then
    jq -c --arg region "$region" '
      (.data.items // .items // []) as $items
      | {region: $region, modelCount: ($items | length), items: $items}
    ' "$response" >> "$successes"
  else
    jq -cn --arg region "$region" --rawfile error "$tmp_dir/$region.err" \
      '{region: $region, error: ($error | rtrimstr("\n"))}' >> "$failures"
  fi
done

regions_object=$(jq -s 'map({key: .region, value: {modelCount: .modelCount, items: .items}}) | from_entries' "$successes")
failures_array=$(jq -s '.' "$failures")

jq -n \
  --arg generated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg profile "$profile" \
  --argjson regions "$regions_object" \
  --argjson failures "$failures_array" \
  '{
    metadata: {
      generatedAt: $generated_at,
      source: "OCI CLI generative-ai model-collection list-models",
      profile: $profile,
      scope: "public OC1 regions queryable by the configured profile"
    },
    regions: $regions,
    failures: $failures
  }' > "$output"

if [[ -n "$catalog_output" ]]; then
  jq '
    def model_records:
      [.regions | to_entries[] | .key as $region | .value.items[] | . + {__region: $region}]
      | sort_by(.displayName)
      | group_by(.displayName)
      | map(
          . as $entries
          | $entries[0] as $first
          | {
              name: $first.displayName,
              id: $first.displayName,
              provider: $first.vendor,
              capabilities: ([$entries[].capabilities[]?] | unique | sort),
              type: $first.type,
              isLongTermSupported: ([$entries[].isLongTermSupported] | all),
              isImageTextToTextSupported: ([$entries[].isImageTextToTextSupported] | any),
              regionalInventory: (
                reduce $entries[] as $entry ({};
                  .[$entry.__region] = {
                    lifecycleState: $entry.lifecycleState,
                    lifecycleDetails: $entry.lifecycleDetails,
                    timeCreated: $entry.timeCreated,
                    timeDeprecated: $entry.timeDeprecated,
                    timeOnDemandRetired: $entry.timeOnDemandRetired,
                    timeDedicatedRetired: $entry.timeDedicatedRetired,
                    dedicatedAiClusterShapes: [
                      $entry.compatibleDedicatedAiClusterShapes[]?
                      | {name, isDefault, quotaUnit}
                    ]
                  }
                )
              )
            }
        );
    model_records as $all
    | {
        metadata: {
          generatedAt: .metadata.generatedAt,
          source: .metadata.source,
          scope: .metadata.scope,
          limitations: [
            "CLI output is the sole source for this snapshot.",
            "OCI CLI does not expose context windows, model tiers, use-case descriptions, or a definitive per-region on-demand access mode.",
            "regionalInventory records observed lifecycle and dedicated-cluster shapes; it must not be treated as the models.json regions access map."
          ],
          successfulRegions: (.regions | keys | sort),
          failedRegions: [.failures[].region]
        },
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

printf 'Wrote %s successful region(s) and %s failed region(s) to %s\n' \
  "$(jq -s 'length' "$successes")" \
  "$(jq -s 'length' "$failures")" \
  "$output"
