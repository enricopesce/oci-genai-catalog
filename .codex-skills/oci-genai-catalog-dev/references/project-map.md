# Project Map

## Repo shape

- `index.html`: only app shell; contains all CSS, markup, wizard UI, filter UI, and inline JS.
- `models.json`: native OCI catalog source of truth.
- `imported-models.json`: imported/open-weight catalog source of truth.
- `sw.js`: small navigation-only service worker.
- `README.md`: public-facing project description.
- `AGENTS.md`: repository-level Codex guidance loaded automatically at session start.
- `.codex-skills/oci-genai-catalog-dev/`: local maintenance skill, references, and audit helper.

## Runtime flow

1. `index.html` clears all `tbody` elements inside `#referenceView`.
2. It fetches `models.json` and `imported-models.json` with `Promise.all(...)`.
3. `renderAll()` fills native chat/embed/rerank sections from `models.json`.
4. `renderImported()` fills imported family tables from `imported-models.json`.
5. The row renderers attach normalized role, capability, workload, availability, and hardware filter metadata derived from JSON fields.
6. `initFilters()` snapshots that metadata and applies scope-aware structured filtering with faceted option counts.
7. Wizard data is derived from JSON, not from the static recommendation cards, and wizard results can apply an equivalent workload/region/deployment preset to the catalog.

## Fields that matter for behavior

- Native wizard behavior depends on `wizardTasks`, `wizardTier`, `wizardCtx`, `wizardWhy`, `regions`, `callType`, and `fineTunable`.
- Native row rendering normalizes `reasoning || thinking` and `toolUse || agentic`.
- Imported rows depend on `family.id`, `badge`, `label`, and each model's `type`, `params`, `activeParams`, `contextWindowLabel`, `contextClass`, `clusterShape`, and `clusterClass`.

## Hardcoded sync points in `index.html`

- Header updated date.
- JSON-LD `dateModified`.
- Stat-bar counts.
- Imported-section summary counts (`provider families` and `models`).
- Footnote data-source date.
- Provider/family mount points used by `renderAll()` and `renderImported()`.

## Known traps

- Fetch failure leaves the page with empty tables because the script clears table bodies before loading data.
- Imported-model HTML rows are duplicated fallback content. Runtime replaces them, so JSON edits are the real data changes.
- Catalog filters depend on `filterRowAttrs()` metadata emitted by every runtime row renderer. Keep primary roles separate from overlapping capabilities, and use workload task metadata for wizard-to-catalog handoff.
- Hosted and importable models intentionally expose different infrastructure facets: hosted models have lifecycle, deployment, and region metadata; importable models have family and recommended GPU hardware. Both scopes can expose context and capability facets.
- Region options include geographic groups as well as exact OCI regions. Regional deployment matching must accept a model only when at least one region in the selected group supports the selected access mode.
- Embedding recommendations ignore tier, deployment, and region filtering even though the wizard still asks those questions.
- In managed Codex workspaces, `.codex/` and `.agents/` may be mounted read-only. Use root `AGENTS.md` as the durable integration point unless the environment allows project-local `.codex/config.toml` or `.agents/skills`.

## Practical commands

- Audit data sync points:
  - `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .`
- Serve locally:
  - `python3 -m http.server 8080`
- Count current model totals quickly:
  - `jq '{chat: (.chatModels|length), embed: (.embeddingModels|length), rerank: (.rerankModels|length)}' models.json`
  - `jq '{families: (.families|length), imported: ([.families[].models[]] | length)}' imported-models.json`
