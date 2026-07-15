# OCI GenAI Catalog

> **Live site → [enricopesce.github.io/oci-genai-catalog](https://enricopesce.github.io/oci-genai-catalog/)**

A single-page reference cataloguing the current **Oracle Cloud Infrastructure (OCI) Generative AI** lineup for commercial OCI regions (OC1), including active models and deprecated models still listed by Oracle, verified 15 July 2026. The site loads one published runtime data file: `catalog.json`.

## What's inside

| Section | Details |
|---------|---------|
| **OCI CLI operational inventory** | 68 unique pretrained offering IDs observed across 13 queryable subscribed regions, including chat, embedding, rerank, voice, video, generation, and safeguard capabilities |
| **Chat models** | 27 pretrained chat models across Cohere, Google, Meta, OpenAI, and xAI; 14 active and 13 deprecated |
| **Embedding models** | 9 Cohere Embed models; Embed 4 active and Embed v3 variants deprecated |
| **Rerank models** | 3 Cohere rerank models: Rerank 4.0 Fast and Pro active; Rerank 3.5 deprecated |
| **Imported models** | 97 compatible/importable models across 12 OCI Model Import families |
| **Selection wizard** | Guided 4-step model picker with a handoff to all matching catalog rows |
| **Use cases** | Separate decision guide for workload, deployment, and regional scenarios |

**Columns covered:** Model ID · Tier · Context window · Multimodal · Tool use · Fine-tuning · Reasoning · Status · Best for

## Features

- Canonical pretrained inventory records all 68 OCI CLI-observed model IDs, their capabilities, lifecycle states, regional observations, dedicated-unit Limits data, and failed regional queries
- Documentation-enriched comparison views cover 27 chat models, 9 embedding models, and 3 rerank models with descriptive fields unavailable from OCI CLI
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

Authenticated OCI CLI responses are the primary source for pretrained offering inventory, capabilities, lifecycle, regional observations, and dedicated-unit Limits data. [OCI official documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/) is used as the source for imported-model compatibility, recommended unit shapes, explicit GPU counts, and other fields the CLI model listing does not expose.

## Development

This is a fully static site. Serve it locally from the repository root with:

```bash
python3 -m http.server 8080
```

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

The generated `genai-offering-cli.json` is ignored by Git. It combines the raw model offering returned by `list-models` with regional `dedicated-unit-*` values from the `ai-generative` Limits service; failed or unsupported queries are retained in `failures`. Region queries run with bounded concurrency, configurable through `--parallel`, and skip OCI CLI retries so unavailable endpoints do not stall a full scan. Limits describe the tenancy's regional quota dimensions and values; they do not prove capacity or provide model-to-shape compatibility.

To also produce a CLI-only pretrained-inventory snapshot, add `--catalog-output models-cli.json`. It is a local verification input, not a published site asset; `catalog.json` is the one runtime catalog file. The CLI-only snapshot deliberately records unavailable fields as limitations rather than inferring them from documentation.

## Pretrained Model Providers

| Provider | Models |
|----------|--------|
| [Cohere](https://cohere.com) | Command A Reasoning, Command A Vision, Command A; deprecated Command R+/R; Embed 4 active, Embed v3 deprecated; Rerank 4.0 active and Rerank 3.5 deprecated |
| [Google](https://deepmind.google/gemini) | Gemini 2.5 Pro, Flash, Flash-Lite |
| [Meta](https://ai.meta.com/llama/) | Llama 4 Maverick, Llama 4 Scout, Llama 3.3 70B; deprecated Llama 3.2 Vision and Llama 3.1 405B |
| [OpenAI](https://openai.com) | gpt-oss-120b, gpt-oss-20b |
| [xAI](https://x.ai) | Grok 4.3, Grok 4.20, Grok 4.20 Multi-Agent; deprecated Grok 4, Grok 4 Fast, Grok 4.1 Fast, Grok 3 family, Grok Code Fast 1 |

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
