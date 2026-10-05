---
name: oci-genai-catalog-dev
description: "Maintain the OCI GenAI Catalog project. Use when Codex needs to continue development on this static OCI model catalog: updating index.html, syncing catalog.json, changing the guided-selection wizard or filter chips, reconciling hardcoded dates and counts with JSON data, or checking whether README.md and the local maintenance docs still reflect the current runtime architecture."
---

# OCI GenAI Catalog Dev

## Overview

Treat `catalog.json` as the single published local snapshot, with `pretrained` and `imported` sections, and treat `index.html` as the UI shell plus all client-side rendering logic. `pretrained.operationalModels` preserves the complete CLI-observed inventory as validation evidence; the chat, embedding, and rerank arrays are presentation views. Start every catalog data refresh with the two official Oracle pages below, then run `scripts/export-pretrained-model-matrix.sh` across all subscribed regions for additional operational observations.

- Official primary sources, always checked first:
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/imported-models.htm` — compatible imported models.
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/model-endpoint-regions.htm` — pretrained regional and serving-mode availability.
- Use authenticated OCI CLI/API/SDK as the second step for validation and extra observations. Preserve differences and failed queries; do not let one tenancy's scan silently replace Oracle's published catalog. Other Oracle pages may supply details outside the two primary pages, with explicit field provenance.

From the repository root, start by running `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .` unless the task is a very small copy-only change.

## Workflow

### Establish the current state

- Inspect the repository root directly; helper docs can drift, so confirm behavior from the code and JSON files.
- Read `.codex-skills/oci-genai-catalog-dev/references/project-map.md` when the task touches data sync, rendering, filters, wizard behavior, service-worker behavior, or stale docs.
- Check the worktree before editing so you do not overwrite user changes.

### Refresh official sources first

- Read the two official primary pages above and record their findings and review date before changing catalog data.
- Next run `scripts/export-pretrained-model-matrix.sh --compartment-id 'COMPARTMENT_OCID' --output genai-offering-cli.json --catalog-output models-cli.json`. Preserve failed regional queries and do not silently interpret a failed query as an empty region.
- Use CLI/API/SDK output to validate offering IDs and capture account-specific capabilities, lifecycle timestamps, regional observations, and Limits dimensions. Record discrepancies with the official pages for review rather than silently overriding them.
- Rebuild `catalog.json.pretrained.operationalModels`, `clusterSizingByRegion`, and `scanFailures` from each authenticated CLI scan as validation evidence, then reconcile the chat, embedding, and rerank views against the primary pages and other clearly attributed Oracle detail pages.
- Edit `catalog.json.imported` for imported/open-weight families and models.
- Keep JSON metadata aligned with actual provenance: name the two official pages as primary sources, and identify CLI commands and scan timestamps as validation and extra evidence.
- Only edit the imported-model HTML rows in `index.html` when the page structure itself changes. Runtime rendering clears and replaces those rows from JSON on load.

### Keep `index.html` in sync with JSON-backed data

- Update hardcoded sync points after data changes:
  - header "Updated ..." copy
  - JSON-LD `dateModified`
  - imported-model intro counts
  - footnote "last updated ..." copy
  - footnote data-source links when the upstream OCI source pages change
- If a new pretrained provider appears, update the provider-specific HTML sections and the hardcoded JS mappings in `renderAll()`, `PROVIDER_LABELS`, and `WIZ_PROVIDER`.
- If a new imported family appears, add a matching `.import-family-title[data-family="..."]` section so `renderImported()` has a mount point.

### Change interactive logic carefully

- Pretrained comparison tables render through `renderAll()` and a single `rowChat()` schema.
- Imported tables render through `renderImported()` using `family.id` and `data-family`.
- Catalog filters are structured. `rowChat()`, `rowEmbed()`, `rowRerank()`, and `rowImported()` emit normalized `data-*` metadata through `filterRowAttrs()`, and `initFilters()` evaluates that metadata instead of scanning rendered row text.
- Keep primary model roles separate from overlapping capabilities. Hosted and importable scopes expose different infrastructure facets, while shared search, context, capability, and workload-task metadata drives faceted counts and wizard-to-catalog handoff.
- Keep status, deployment, exact regional access, capability, context, workload task, imported family, and GPU metadata aligned when renderer fields change.
- Wizard ranking depends on JSON fields such as `wizardTasks`, `wizardTier`, `wizardCtx`, `wizardWhy`, `regions`, `callType`, and `fineTunable`.
- The embedding wizard path is intentionally special-cased and ignores tier, deployment, and region filtering.
- The page clears all table bodies before fetching JSON; fetch failures leave empty tables. Be careful when changing fetch paths or startup order.

### Validate before finishing

- Run `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .` after non-trivial changes.
- If you modify this skill, run `python3 /home/opc/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex-skills/oci-genai-catalog-dev`.
- For UI or behavior changes, serve the repo locally with `python3 -m http.server 8080` from the repository root and exercise the reference view, wizard view, filters, and theme toggle.

### Keep supporting docs honest

- Update `README.md` and `.codex-skills/oci-genai-catalog-dev/references/project-map.md` when architecture or workflow changes materially.
- Treat the code and JSON files as the implementation truth when helper docs drift; use the two official Oracle pages above as the published source authority for the fields they cover.

## References

- Read `.codex-skills/oci-genai-catalog-dev/references/project-map.md` for the repo layout, hardcoded sync points, and recurring maintenance traps.
- Secondary pretrained validation and extra extraction:
  - `scripts/export-pretrained-model-matrix.sh`
  - `oci generative-ai model-collection list-models`
  - `oci limits value list --service-name ai-generative`
- Other Oracle detail pages:
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/pretrained-models.htm`
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/modes.htm`

## Bundled helper

- Use `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .` to compare JSON counts and dates against the hardcoded values still living in `index.html`, and to flag stale project docs that commonly drift.
