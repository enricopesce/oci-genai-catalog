# Project Map

## Repo shape

- `index.html`: only app shell; contains all CSS, markup, the technical catalog, the separate Use Cases view, wizard UI, filter UI, and inline JS.
- `catalog.json`: single runtime snapshot consumed by the site. `pretrained.operationalModels` is the CLI-authoritative inventory of OCI-offered pretrained models; `clusterSizingByRegion` and `scanFailures` preserve sizing observations and failed queries; chat/embed/rerank arrays provide documentation-enriched comparison views; `imported` contains open-weight data and structured GPU shape options.
- `sw.js`: small navigation-only service worker.
- `scripts/export-pretrained-model-matrix.sh`: local OCI CLI exporter for pretrained model offerings and `ai-generative` dedicated-unit Limits data across active subscribed regions; it queries canonical region names with bounded concurrency and can also produce a CLI-only comparison snapshot.
- `README.md`: public-facing project description.
- `AGENTS.md`: repository-level Codex guidance loaded automatically at session start.
- `.codex-skills/oci-genai-catalog-dev/`: local maintenance skill, references, and audit helper.

## Runtime flow

1. `index.html` clears all `tbody` elements inside `#referenceView`.
2. It fetches `catalog.json`.
3. `renderAll()` fills documentation-enriched pretrained chat/embed/rerank sections from `catalog.json.pretrained`.
4. `renderOperational()` fills the complete OCI CLI operational inventory from `catalog.json.pretrained.operationalModels`.
5. `renderImported()` fills imported family tables from `catalog.json.imported`, including structured shape and GPU options.
6. The row renderers attach normalized role, capability, workload, availability, and hardware filter metadata derived from JSON fields.
7. The primary view switcher keeps Technical Tables, Guided Selection, and the static Use Cases decision guide in separate top-level views.
8. `initFilters()` snapshots that metadata and applies an always-visible structured filter panel. A required deployment-path selector first chooses on-demand access or dedicated clusters. On-demand displays eligible hosted models directly; dedicated displays the combined hosted and Model Import catalog. Faceted controls then narrow the results, and one Capability selector exposes both primary roles and overlapping feature capabilities.
9. Wizard data is derived from JSON, not from the static recommendation cards, and wizard results can apply an equivalent workload/deployment preset to the catalog; its deployment answer activates the matching primary selector, and dedicated presets open the combined cluster scope. The wizard's broad geographic answer is not transferred into the catalog's exact-region selector.

## Data-source hierarchy

1. Authenticated OCI CLI/API responses for pretrained offerings are the operational authority. Scan every subscribed `READY` region and retain both successes and failures.
2. Rebuild `catalog.json.pretrained.operationalModels`, `clusterSizingByRegion`, scan metadata, and `scanFailures` from CLI-observed IDs, vendors, capabilities, lifecycle fields, regional inventory, and `ai-generative` Limits data.
3. Use Oracle documentation only for verification or extension fields unavailable from native commands. Label documentation-derived fields and never use documentation to override contradictory CLI observations.
4. Do not interpret a successful empty response, an authorization failure, a missing endpoint, and a transient error as the same state.

## Fields that matter for behavior

- Pretrained wizard behavior depends on `wizardTasks`, `wizardTier`, `wizardCtx`, `wizardWhy`, `regions`, `callType`, and `fineTunable`.
- Pretrained row rendering normalizes `reasoning || thinking` and `toolUse || agentic`.
- Imported rows depend on `family.id`, `badge`, `label`, and each model's `type`, `params`, `activeParams`, `contextWindowLabel`, `contextClass`, `clusterShape`, `clusterClass`, and structured `dedicatedClusterOptions`; their type also supplies workload metadata for cluster-scope wizard handoff.

## Hardcoded sync points in `index.html`

- Header updated date.
- JSON-LD `dateModified`.
- Imported-section summary counts (`provider families` and `models`).
- Footnote data-source date.
- Provider/family mount points used by `renderAll()` and `renderImported()`.

## Known traps

- Fetch failure leaves the page with empty tables because the script clears table bodies before loading data.
- Imported-model HTML rows are duplicated fallback content. Runtime replaces them, so JSON edits are the real data changes.
- Catalog filters depend on `filterRowAttrs()` metadata emitted by every runtime row renderer. Keep primary roles separate from overlapping capabilities in row metadata even though the UI combines both in one Capability selector; role options use `role:`-prefixed values. Use workload task metadata for wizard-to-catalog handoff.
- Hosted and importable models expose different infrastructure facets: hosted models have lifecycle, deployment, and region metadata; importable models have family and recommended GPU hardware. The deployment-path selector owns the on-demand/dedicated distinction. Dedicated activates the combined cluster scope, which includes dedicated-capable hosted rows plus all Model Import rows; one GPU model facet lists and filters exact model/count combinations.
- Region filtering remains hosted-only because the imported-model snapshot does not contain regional availability. The catalog selector lists only exact OCI region names and identifiers; the wizard retains broad geographic groups for its simplified recommendation step and does not transfer that coarse answer into the exact-region filter.
- Facet options remain cascading: zero-result choices disappear, but result counts are intentionally not shown in option labels.
- Pretrained row metadata retains exact region access for filtering, but the comparison tables intentionally omit the verbose Regions badge column. Empty table headings are hidden with their tables, and the entire results block is hidden when no model matches.
- The CLI-authoritative operational inventory is not filterable presentation data. It remains visible only in the unfiltered default on-demand catalog and is hidden whenever a catalog filter or the dedicated-cluster path is active.
- Embedding recommendations ignore tier, deployment, and region filtering even though the wizard still asks those questions.
- In managed Codex workspaces, `.codex/` and `.agents/` may be mounted read-only. Use root `AGENTS.md` as the durable integration point unless the environment allows project-local `.codex/config.toml` or `.agents/skills`.

## Practical commands

- Audit data sync points:
  - `python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .`
- Serve locally:
  - `python3 -m http.server 8080`
- Count current model totals quickly:
  - `jq '{operational: (.pretrained.operationalModels|length), chat: (.pretrained.chatModels|length), embed: (.pretrained.embeddingModels|length), rerank: (.pretrained.rerankModels|length), families: (.imported.families|length), imported: ([.imported.families[].models[]] | length)}' catalog.json`
- Export pretrained model and dedicated-unit Limits data from an authenticated OCI CLI profile before every catalog data refresh:
  - `scripts/export-pretrained-model-matrix.sh --compartment-id 'YOUR_COMPARTMENT_OCID' --output genai-offering-cli.json --catalog-output models-cli.json`
