# Changelog

All notable updates to this repository are tracked here.

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
