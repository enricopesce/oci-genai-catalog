# OCI GenAI Catalog

> **Live site → [enricopesce.github.io/oci-genai-catalog](https://enricopesce.github.io/oci-genai-catalog/)**

A single-page reference cataloguing the active **Oracle Cloud Infrastructure (OCI) Generative AI** lineup for commercial OCI regions (OC1), verified April 2026.

## What's inside

| Section | Details |
|---------|---------|
| **Chat models** | Cohere Command A family · Google Gemini 2.5 · Meta Llama 4 · OpenAI gpt-oss · xAI Grok 4 |
| **Embedding models** | Cohere Embed v3 & v4 (text + multimodal) |
| **Rerank model** | Cohere Rerank 3.5 |
| **Imported models** | 79 community/open-weight models via OCI Model Catalog |
| **Selection wizard** | Guided 4-step model picker (use case → quality/speed → deployment → region) |

**Columns covered:** Model ID · Tier · Context window · Multimodal · Tool use · Fine-tuning · Reasoning · Status · Best for

## Features

- 5 native providers + 79 imported models across 8 provider families
- Commercial OCI regions (OC1) covered in the UI; sovereign and government regions are not yet modeled
- Dark / Light mode toggle (preference saved in `localStorage`)
- Guided model selection wizard
- Fully static — no JavaScript framework, no build step
- Mobile responsive

## Data source

All data sourced from the [OCI official documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/).

## Native Providers

| Provider | Models |
|----------|--------|
| [Cohere](https://cohere.com) | Command A Reasoning, Command A Vision, Command A, Command R+, Command R, Embed v4/v3, Rerank 3.5 |
| [Google](https://deepmind.google/gemini) | Gemini 2.5 Pro, Flash, Flash-Lite |
| [Meta](https://ai.meta.com/llama/) | Llama 4 Maverick, Llama 4 Scout, Llama 3.3 70B, Llama 3.2 90B/11B Vision, Llama 3.1 405B |
| [OpenAI](https://openai.com) | gpt-oss-120b, gpt-oss-20b |
| [xAI](https://x.ai) | Grok 4, Grok 4 Fast, Grok 4.1 Fast, Grok 4.20, Grok 4.20 Multi-Agent, Grok 3, Grok 3 Fast, Grok 3 Mini, Grok 3 Mini Fast, Grok Code Fast 1 |

## Imported Models

| Provider | Models |
|----------|--------|
| [Alibaba](https://qwen.readthedocs.io) | Qwen3, Qwen3-VL, Qwen2.5, QwQ families |
| [DeepSeek](https://deepseek.com) | DeepSeek-R1-Distill-Qwen-32B |
| [Google (Gemma)](https://ai.google.dev/gemma) | Gemma 3 (270M–27B), Gemma 2 (2B–27B) |
| [Microsoft](https://microsoft.com) | Phi-4, Phi-3 family |
| [Mistral](https://mistral.ai) | Mixtral 8x7B, Mistral Nemo, Mistral 7B, E5-Mistral |
| [NVIDIA](https://nvidia.com) | Nemotron Super 120B, Nano 30B, Llama Nemotron 70B |
