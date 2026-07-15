# Changelog

All notable updates to this repository are tracked here.

## 2026-07-15

- Re-verified native OCI Generative AI model inventory, lifecycle status, and OC1 regional availability against Oracle's public pretrained-model and regional-availability documentation.
- Re-verified all 12 Oracle-tested Model Import families and their 97 compatible models against the current Oracle documentation; no inventory changes were published upstream.
- Advanced the JSON source snapshot and catalog freshness markers to 15 July 2026.
- Replaced the header's stale model-count claim with a direct link to the native catalog JSON reference.

## 2026-07-10

- Added a deployment-first catalog selector with two explicit paths—on-demand access and dedicated clusters—before users refine by capability or infrastructure facets.
- Removed the secondary source-scope switch: on-demand now shows eligible hosted models directly, while dedicated shows the combined hosted and Model Import catalog with aligned wizard handoff and GPU filtering.
- Removed deployment-card counts, the filtered “x of y models” line, and the provider/role stat cards to keep the catalog focused on the model tables.
- Moved the static Use-Case Selection Guide out of the technical catalog into its own top-level Use Cases view.
- Removed parenthesized result counts from filter options and replaced geographic-group region choices with exact official OCI region names and identifiers.
- Re-verified native and imported catalog data against current public Oracle documentation, including source pages updated through 6 July 2026.
- Added MiniMax, Moonshot AI Kimi, and Z.ai GLM imported-model families.
- Added Oracle-tested Qwen3 VL FP8, Mistral Medium 3.5, Devstral 2, and NVIDIA Nemotron Nano entries; removed two Phi 128K variants no longer listed by Oracle.
- Updated current DeepSeek and Gemma recommended cluster shapes, increasing imported coverage from 88 models across 9 families to 97 models across 12 families.
- Corrected Phoenix availability for `cohere.embed-multilingual-v3.0` and Sao Paulo availability for `cohere.rerank.v3-5`.
- Synced catalog dates, dashboard counts, imported-family mount points, badge styles, and README summaries.
- Replaced text-matching filter chips with structured hosted/importable views, model search, role and capability facets, active-by-default lifecycle filtering, regional deployment matching, context thresholds, imported GPU filters, dynamic counts, and complete empty-section handling.
- Simplified catalog discovery around primary model roles and intent-aware use-case search; moved infrastructure facets into an inline advanced panel with live counts, cascading region/deployment availability, removable filter chips, deprecated-model opt-in, and accurate active/total labels.
- Added a guided-selection handoff that opens every matching active catalog model with the wizard workload, deployment, and hosted geographic region filters already applied.
- Hid zero-result role and filter choices while preserving selected zero-result values and always keeping each filter's neutral reset choice available; promoted the filter panel to an always-visible, non-collapsible standard catalog view.
- Added a combined Clusters scope for dedicated-capable hosted models and compatible Model Import models, including GPU filtering, direct switching from the hosted deployment selector, and dedicated-wizard handoff for imported workloads.
- Consolidated the separate Model role row into the Capability selector, which now exposes chat, embedding, rerank, image, and audio roles alongside vision, reasoning, coding, tool-use, and fine-tuning capabilities.
- Hid every empty model section and the complete results area when no models match, and removed the verbose Regions badge column from native model tables while retaining region-based filtering.
- Made the catalog stat bar reflect only currently visible filtered records and hide zero-count cards, replacing misleading global totals after capability, scope, search, or infrastructure filters are applied.

## 2026-06-24

- Re-verified OCI Generative AI catalog data against current public Oracle documentation using parallel focused research agents.
- Added imported `Qwen/Qwen3-Next-80B-A3B-Instruct`, `deepseek-ai/DeepSeek-V4-Pro`, `deepseek-ai/DeepSeek-V4-Flash`, and `google/medgemma-27b-text-it`, increasing imported-model coverage from 84 to 88 models.
- Updated imported Qwen and Gemma recommended dedicated AI cluster shape coverage where Oracle now lists multiple compatible shapes.
- Marked `cohere.rerank.v3-5` (`Rerank 3.5`) as deprecated while keeping it visible in the reference catalog.
- Updated the guided wizard and static use-case guide to recommend active models only.
- Synced catalog dates, imported-model counts, dashboard copy, and README model summaries to the 24 June 2026 refresh.
- Documented that future non-trivial repository changes should update `CHANGELOG.md`.

## 2026-06-15

- Synced OCI model reference data against the current public Oracle documentation.
- Added imported `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4` with B200_X4 recommended cluster shape.
- Added imported `openai/whisper-large-v3-turbo` for audio-to-text workloads with H100_X1 and A100_80G_X1 recommended cluster shapes.
- Increased imported-model coverage from 82 to 84 models and added a separate OpenAI Whisper import family.
- Updated `Rerank 3.5` to active status and corrected Meta Llama 3.3 70B commercial-region availability, including UAE Central (Abu Dhabi).
- Normalized the static-site source-date footnote and updated the catalog audit helper to recognize imported audio model types.

## 2026-05-17

- Synced OCI model reference data against the current public Oracle documentation.
- Added UAE Central (`me-abudhabi-1`) to the commercial OC1 region set and selection wizard region matching.
- Added `cohere.rerank-v4.0-fast` and `cohere.rerank-v4.0-pro` to the native rerank catalog.
- Added imported `Qwen/Qwen3.6-35B-A3B`, `Qwen/Qwen3.5-9B`, and `google/gemma-4-31B-it`, increasing imported-model coverage from 79 to 82 models.
- Marked older Cohere Command R, Meta Llama 3.2/3.1, xAI Grok, and Cohere Embed v3 entries as deprecated while keeping them visible in the catalog.

## 2026-05-07

- Synced OCI model reference data against the current Oracle documentation.
- Added `xai.grok-4.3` with 1M context, multimodal reasoning, on-demand availability in Ashburn, Chicago, and Phoenix.
- Re-verified imported model coverage against Oracle's Compatible Models for Import documentation; no imported model count changes.
- Cleaned page attribution metadata, author metadata, and footer disclaimer copy for the static site.

## 2026-04-29

- Improved table accessibility with semantic headings, keyboard-focusable table wrappers, ARIA labels, stronger light-theme contrast tokens, and a `main` landmark.
- Updated the OCI catalog development skill docs with source-of-truth workflow, official OCI source pages, audit command paths, and validation guidance.

## 2026-04-27

- Synced OCI model reference data against the current Oracle documentation.
- Added `ap-hyderabad-1` to `Rerank 3.5` in `models.json` to match Oracle's current regional availability for Cohere Rerank 3.5.
- Re-verified native and imported model inventories against the Oracle pretrained, regional availability, and imported-model documentation pages.
