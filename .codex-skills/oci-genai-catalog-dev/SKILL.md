---
name: oci-genai-catalog-dev
description: "Maintain the OCI GenAI Catalog project. Use when Codex needs to continue development on this static OCI model catalog: updating index.html, syncing models.json or imported-models.json, changing the guided-selection wizard or filter chips, reconciling hardcoded dates and counts with JSON data, or checking whether README.md and the local maintenance docs still reflect the current runtime architecture."
---

# OCI GenAI Catalog Dev

## Overview

Treat `models.json` and `imported-models.json` as the local catalog data sources of truth, and treat `index.html` as the UI shell plus all client-side rendering logic. Those JSON files are maintained from OCI public documentation, primarily:

- Native OCI models:
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/pretrained-models.htm`
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/model-endpoint-regions.htm`
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/modes.htm`
- Imported/open-weight models:
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/imported-models.htm`

From the repository root, start by running `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .` unless the task is a very small copy-only change.

## Workflow

### Establish the current state

- Inspect the repository root directly; helper docs can drift, so confirm behavior from the code and JSON files.
- Read `.codex-skills/oci-genai-catalog-dev/references/project-map.md` when the task touches data sync, rendering, filters, wizard behavior, service-worker behavior, or stale docs.
- Check the worktree before editing so you do not overwrite user changes.

### Update the real source of truth first

- Verify changes against the OCI docs pages listed in the Overview, then update the local JSON snapshots.
- Edit `models.json` for native OCI chat, embedding, and rerank data.
- Edit `imported-models.json` for imported/open-weight families and models.
- Keep each JSON file's `metadata.source` aligned with the OCI page it was derived from.
- Only edit the imported-model HTML rows in `index.html` when the page structure itself changes. Runtime rendering clears and replaces those rows from JSON on load.

### Keep `index.html` in sync with JSON-backed data

- Update hardcoded sync points after data changes:
  - header "Updated ..." copy
  - JSON-LD `dateModified`
  - stat-bar counts
  - imported-model intro counts
  - footnote "last updated ..." copy
  - footnote data-source links when the upstream OCI source pages change
- If a new native provider appears, update the provider-specific HTML sections and the hardcoded JS mappings in `renderAll()`, `PROVIDER_LABELS`, and `WIZ_PROVIDER`.
- If a new imported family appears, add a matching `.import-family-title[data-family="..."]` section so `renderImported()` has a mount point.

### Change interactive logic carefully

- Native tables render through `renderAll()` and a single `rowChat()` schema.
- Imported tables render through `renderImported()` using `family.id` and `data-family`.
- Filter chips are text-based; new filter controls only work if the row text or `data-tags` exposes matching terms.
- Wizard ranking depends on JSON fields such as `wizardTasks`, `wizardTier`, `wizardCtx`, `wizardWhy`, `regions`, `callType`, and `fineTunable`.
- The embedding wizard path is intentionally special-cased and ignores tier, deployment, and region filtering.
- The page clears all table bodies before fetching JSON; fetch failures leave empty tables. Be careful when changing fetch paths or startup order.

### Validate before finishing

- Run `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .` after non-trivial changes.
- If you modify this skill, run `python3 /home/opc/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex-skills/oci-genai-catalog-dev`.
- For UI or behavior changes, serve the repo locally with `python3 -m http.server 8080` from the repository root and exercise the reference view, wizard view, filters, and theme toggle.

### Keep supporting docs honest

- Update `README.md` and `.codex-skills/oci-genai-catalog-dev/references/project-map.md` when architecture or workflow changes materially.
- Treat the code and JSON files as the source of truth when helper docs drift.

## References

- Read `.codex-skills/oci-genai-catalog-dev/references/project-map.md` for the repo layout, hardcoded sync points, and recurring maintenance traps.
- Upstream OCI source pages:
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/pretrained-models.htm`
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/model-endpoint-regions.htm`
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/modes.htm`
  - `https://docs.oracle.com/en-us/iaas/Content/generative-ai/imported-models.htm`

## Bundled helper

- Use `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .` to compare JSON counts and dates against the hardcoded values still living in `index.html`, and to flag stale project docs that commonly drift.
