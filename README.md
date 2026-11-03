# OCI GenAI Catalog

> **Live site → [enricopesce.github.io/oci-genai-catalog](https://enricopesce.github.io/oci-genai-catalog/)**

A single-page reference cataloguing **Oracle Cloud Infrastructure (OCI) Generative AI** models for commercial OCI regions (OC1), including active and deprecated entries. The published `catalog.json` snapshot is dated 3 November 2026.

## What's inside

| Section | Details |
|---------|---------|
| **OCI CLI validation inventory** | 66 unique pretrained model IDs observed in the November scan, including chat, embedding, rerank, voice, video, generation, and safeguard capabilities |
| **Model Discovery** | 22 discovered IDs from 34 successful region queries across 41 subscribed regions; explicit serving modes, supported APIs, modalities, and parameters |
| **Chat models** | 29 pretrained chat models across Cohere, Google, Meta, OpenAI, and xAI |
| **Embedding models** | 9 Cohere Embed models; Embed 4 active and Embed v3 variants deprecated |
| **Rerank models** | 3 Cohere rerank models: Rerank 4.0 Fast and Pro active; Rerank 3.5 deprecated |
| **Imported models** | 97 compatible/importable models across 12 OCI Model Import families |
| **Selection wizard** | Guided 4-step model picker with a handoff to all matching catalog rows |
| **Use cases** | Separate decision guide for workload, deployment, and regional scenarios |

**Columns covered:** Model ID · Tier · Context window · Multimodal · Tool use · Fine-tuning · Reasoning · Status · Best for

## Features

- CLI validation inventory records the observed pretrained model IDs, their capabilities, lifecycle states, regional observations, dedicated-unit Limits data, and failed regional queries
- Comparison views cover 29 chat models, 9 embedding models, and 3 rerank models with descriptive fields unavailable from OCI CLI
- Every imported model has structured dedicated-cluster alternatives with `unitShape`, `gpuType`, `gpuCount`, required limit units, limit name, and AI unit count
- 97 imported models across 12 Model Import families, including Qwen, DeepSeek, Gemma, Llama, MiniMax, Mistral, Kimi, Nemotron, Whisper, gpt-oss, and GLM entries
- Commercial OCI regions (OC1) covered in the UI, including UAE Central (Abu Dhabi); sovereign and government regions are not yet modeled
- Dark / Light mode toggle (preference saved in `localStorage`)
- Guided model selection wizard with a one-click handoff to the matching catalog scope and workload filters
- Dedicated Use Cases view, separated from the technical catalog tables
- Intent-aware catalog search across model names, IDs, providers, and use cases
- Deployment-first catalog filtering that clearly separates on-demand access from dedicated clusters, followed by capability/role, exact OCI region, context, lifecycle, and GPU refinements with cascading availability
- Semantic headings and keyboard-focusable table sections for accessibility
- Fully static — no JavaScript framework, no build step
- Mobile responsive

## Data sources

The official primary sources are Oracle's [Compatible Models for Import](https://docs.oracle.com/en-us/iaas/Content/generative-ai/imported-models.htm) and [Generative AI Models by Region](https://docs.oracle.com/en-us/iaas/Content/generative-ai/model-endpoint-regions.htm) pages. Start with these for imported-model compatibility and pretrained regional and serving-mode availability. Authenticated OCI CLI/API/SDK scans follow as validation and extra operational evidence for offering IDs, capabilities, lifecycle, regional observations, and dedicated-unit Limits data. Preserve disagreements and failed queries rather than treating one tenancy's scan as the official catalog.

## Development

This is a fully static site. Serve it locally from the repository root with:

```bash
python3 -m http.server 8080
```

Open the HTTP URL (for example, `http://localhost:8080/`) rather than opening `index.html` directly: browsers restrict fetching the adjacent JSON from `file://` pages. Catalog request failures now show an explicit error and recovery instructions. Browser storage can be disabled in a sandboxed preview without interrupting model loading.

Codex project guidance lives in `AGENTS.md`. The local catalog-maintenance workflow, reference map, and audit helper live under `.codex-skills/oci-genai-catalog-dev/`.

Run the catalog audit after non-trivial data, UI, or documentation changes:

```bash
python3 .codex-skills/oci-genai-catalog-dev/scripts/catalog_audit.py --repo .
```

To capture pretrained-model and dedicated-unit Limits data from an authenticated OCI CLI profile, run:

```bash
scripts/export-pretrained-model-matrix.sh \
  --compartment-id 'YOUR_COMPARTMENT_OCID' \
  --parallel 6 \
  --output genai-offering-cli.json \
  --catalog-output models-cli.json
```

The exporter uses [Model Discovery](https://docs.oracle.com/en-us/iaas/Content/generative-ai/model-discovery.htm) as the regional discovery method, querying `oci generative-ai model-discovery-collection list-model-discovery --all` for every subscribed `READY` region. Use a current OCI CLI that exposes this command (verified with 3.95.1). `--region` selects the service endpoint; **`--region-parameterconflict` filters the model's deployment region**. Omitting the latter returns models across all regions. Returned availability arrays can still contain other deployment regions, so the exporter preserves the complete response. No retirement filter is applied.

`genai-offering-cli.json` is ignored by Git. It stores discovery responses under `modelDiscoveryByRegion`, legacy `list-models` observations under `regions`, dedicated-unit Limits under `clusterSizingByRegion`, and all failed queries under `failures`. Successful empty responses remain separate from failures. Queries use bounded concurrency and connection/read timeouts; the script supports macOS Bash 3.2. Legacy ListModels remains necessary for offering OCIDs and lifecycle states; Limits describe quota rather than capacity or model-to-shape compatibility.

To reconcile the export into a reviewable runtime catalog candidate:

```bash
python3 scripts/sync-discovery-catalog.py genai-offering-cli.json \
  --output /tmp/catalog-candidate.json
```

The reconciler rebuilds the legacy operational inventory, updates successful Limits observations with their dates, retains failures, and stores discovery records in `pretrained.discoveryModels`. Identical model responses are stored once with their endpoint regions. It annotates known presentation models (including their aliases) with observed serving modes, records disagreements with documentation in `metadata.sources.pretrained.modelDiscovery.discrepancies`, and lists unreviewed IDs and presentation IDs not observed by discovery. It preserves documentation-backed presentation regions and never infers retirement from an absent model. Review custom/fine-tuned IDs before publishing a candidate; discovery can return both pretrained and fine-tuned models. Review descriptive fields and synchronize the page dates before replacing `catalog.json`.

The November scan contains 66 legacy model IDs and 22 discovery IDs; these APIs expose different inventories. It retains 15 failures: seven discovery, six legacy model, and two Limits queries. Three serving-mode disagreements remain explicit (Command A Vision in Abu Dhabi; Embed 4 in Frankfurt and Abu Dhabi). The imported snapshot retains its July date; Oracle's current landing page lists SEA-LION, OmniVoice, and MiMo families requiring a separate imported-compatibility refresh. Voice is recorded in the operational/discovery data and regional coverage notes; the presentation views remain chat, embedding, and rerank.

Run offline regression checks for the exporter and reconciler with:

```bash
python3 scripts/test-model-discovery.py
```

`--catalog-output models-cli.json` additionally writes a CLI-only verification snapshot, including raw discovery results. Neither export is a runtime site asset; `catalog.json` remains the single runtime snapshot.

## Pretrained Model Providers

| Provider | Models |
|----------|--------|
| [Cohere](https://cohere.com) | Command A Reasoning, Command A Vision, Command A; deprecated Command R+/R; Embed 4 active, Embed v3 deprecated; Rerank 4.0 active and Rerank 3.5 deprecated |
| [Google](https://deepmind.google/gemini) | Gemini 2.5 Pro, Flash, Flash-Lite |
| [Meta](https://ai.meta.com/llama/) | Llama 4 Maverick, Llama 4 Scout, Llama 3.3 70B; deprecated Llama 3.2 Vision and Llama 3.1 405B |
| [OpenAI](https://openai.com) | gpt-oss-120b, gpt-oss-20b |
| [xAI](https://x.ai) | Grok 4.7, Grok 4.6, Grok 4.3, Grok 4.20, Grok 4.20 Multi-Agent; deprecated Grok 4, Grok 4 Fast, Grok 4.1 Fast, Grok 3 family, Grok Code Fast 1 |

## Imported Models

| Provider | Models |
|----------|--------|
| [Alibaba Qwen](https://qwen.readthedocs.io) | Qwen3 Next, Qwen3.6, Qwen3.5, Qwen3, Qwen3-VL, Qwen2.5, QwQ, Qwen Image, Qwen Embedding families |
| [DeepSeek](https://deepseek.com) | DeepSeek-V4 Pro, DeepSeek-V4 Flash, DeepSeek-R1-Distill-Qwen-32B |
| [Google (Gemma)](https://ai.google.dev/gemma) | MedGemma 27B, Gemma 4 31B, Gemma 3 (270M–27B), Gemma 2 (2B–27B) |
| [Meta Llama](https://ai.meta.com/llama/) | Llama 4, Llama 3.3, Llama 3.2, Llama 3.1, Llama 3, Llama 2 families |
| [Microsoft Phi](https://microsoft.com) | Phi-4, Phi-3 family |
| [Mistral](https://mistral.ai) | Mixtral 8x7B, Mistral Nemo, Mistral 7B, E5-Mistral |
| [NVIDIA Nemotron](https://nvidia.com) | Nemotron Ultra 550B, Super 120B, Nano 30B, Llama Nemotron 70B |
| [OpenAI Whisper](https://openai.com) | Whisper Large V3 Turbo |
| [OpenAI gpt-oss](https://openai.com) | gpt-oss-120b, gpt-oss-20b |
