# AGENTS.md

## Project Shape

- This is a static OCI GenAI Catalog site. There is no package manager, build step, framework, or test runner.
- `index.html` contains the UI shell, CSS, and all client-side rendering and wizard logic.
- `catalog.json` is the single runtime snapshot consumed by the site. Its `pretrained.operationalModels` array is the CLI-authoritative complete inventory of OCI-offered pretrained models; the chat, embedding, and rerank arrays are documentation-enriched presentation views. Its `imported` section contains open-weight model families.
- `sw.js` is a small navigation-only service worker.

## Codex Workflow

- Check `git status --short` before editing and avoid overwriting user changes.
- For work touching catalog data, rendering, filters, wizard behavior, service-worker behavior, or stale docs, read `.codex-skills/oci-genai-catalog-dev/SKILL.md` and `.codex-skills/oci-genai-catalog-dev/references/project-map.md` before making changes.
- Start by running `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .` unless the task is a very small copy-only change.
- Treat authenticated OCI CLI/API responses for pretrained offerings as the primary authority for model IDs, capabilities, lifecycle, regional observations, and service-limit sizing. Run the repository exporter across all subscribed regions before refreshing catalog data.
- Use public Oracle documentation only as a secondary extension and verification source. Documentation must not override contradictory CLI data; fields unavailable from pretrained model commands must be clearly identified as documentation-derived rather than operational truth.
- Update `CHANGELOG.md` for every non-trivial repository change, including data refreshes, UI behavior changes, workflow changes, and documentation updates.

## Editing Rules

- Update `catalog.json.pretrained.operationalModels`, CLI scan metadata, Limits observations, and failures first, then reconcile documentation-enriched views and hardcoded sync points in `index.html`.
- Keep these `index.html` values aligned after data changes: header updated date, JSON-LD `dateModified`, stat counts, imported-model intro counts, footnote date, provider mappings, and imported family mount points.
- Do not edit imported-model fallback HTML rows for data-only changes; runtime rendering replaces them from `catalog.json`.
- Preserve the current static architecture unless the user explicitly asks for a framework or build pipeline.
- Keep README and `.codex-skills/oci-genai-catalog-dev/references/project-map.md` current when architecture or maintenance workflow changes.

## Validation

- Run `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .` after non-trivial changes.
- For UI or behavior changes, serve the repo with `python3 -m http.server 8080` and check the reference view, wizard view, filters, and theme toggle in a browser.
- If modifying the local skill, run `python3 /home/opc/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex-skills/oci-genai-catalog-dev`.

## Git Notes

- `core.hooksPath` is `.githooks`. The pre-commit hook stamps the current short commit hash into the `build-version` meta tag in `index.html` and stages that file.
- Do not revert hook-created `build-version` changes unless the user asks.
