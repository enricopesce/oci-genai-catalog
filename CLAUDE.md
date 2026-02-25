# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository is a **single-file static HTML reference page** (`index.html`) — an OCI Generative AI Model Comparison table covering 30+ models across 5 providers (Cohere, Google, Meta, OpenAI gpt-oss, xAI). No build tools, no dependencies, no package manager.

## Development

To view the page, open `index.html` directly in a browser, or serve it locally:

```bash
python3 -m http.server 8080
# then open http://localhost:8080
```

There is no build, lint, or test step.

## File Structure

Everything lives in `index.html` in three logical blocks:

1. **`<style>` block** — All CSS, using custom properties defined in `:root`
2. **`<body>` content** — Stat bar summary, then one `<table>` per model family, then an embedding table, a rerank table, a Use-Case Selection Guide (matrix cards), a legend, and footnotes
3. No JavaScript — the page is purely static HTML/CSS

## CSS Design System

CSS custom properties (`:root`):
- Colors: `--red` (Oracle brand), `--dark` (page bg), `--panel` / `--panel2` (card surfaces), `--border`, `--text`, `--muted`
- Provider accent colors: `--cohere`, `--google`, `--meta`, `--openai`, `--xai`, `--embed`

Key CSS classes:
- `.badge-{provider}` — colored pill labels (badge-cohere, badge-google, badge-meta, badge-openai, badge-xai, badge-embed)
- `.tier-{level}` — tier indicator styles: `tier-flagship` (★), `tier-balanced` (◉), `tier-fast` (▷), `tier-lite` (○), `tier-spec` (◆)
- `.ctx-{size}` — context window color coding: `ctx-huge` (≥1M, red-orange), `ctx-xl` (256K, orange), `ctx-lg` (128K, gold), `ctx-md` (32K, green), `ctx-sm` (muted)
- `.status-active` (green), `.status-deprecated` (orange), `.status-retired` (red)
- `.yes` (green ✓), `.no` (red/muted ✗)
- `.matrix-card` / `.rec-item` — use-case selection guide cards

## Adding or Updating Models

Each model family has its own `<table>` under a `.section-title` div. Columns vary by family (e.g. Llama tables include Architecture/Total Params/Active Params; xAI tables include Coding Focus/Domain Knowledge). Match the column schema of the relevant family's `<thead>` when inserting a new `<tr>`.

Template for a new chat model row (adapt columns to match the family's thead):
```html
<tr>
  <td class="model-cell">
    <span class="badge badge-{provider}">{Provider}</span><br>
    <span class="model-name">{Model Name}</span>
  </td>
  <td><span class="model-id">{provider.model-id}</span></td>
  <td><span class="tier tier-{level}">{symbol} {Tier Label}</span></td>
  <td><span class="ctx ctx-{size}">{N}K</span></td>
  <td><span class="yes">✓</span></td>   <!-- or <span class="no">✗</span> -->
  <td><span class="status-active">● GA</span></td>
  <td class="best-for">{Use case description}</td>
</tr>
```

Update the stat bar counts (`.stat-num` in the `.stat-bar` div near line 286) whenever the total model counts change.

## Data Source

All model data is sourced from OCI official documentation (`docs.oracle.com/en-us/iaas/Content/generative-ai/`). The page header includes the data date ("February 2026"). Update this when refreshing model data.