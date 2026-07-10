#!/usr/bin/env python3
"""Audit OCI GenAI Catalog hardcoded sync points against JSON source data."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


PROVIDER_SECTION_KEYWORDS = {
    "cohere": "Cohere Family",
    "google": "Google Gemini Family",
    "meta": "Meta Llama Family",
    "openai": "OpenAI gpt-oss Family",
    "xai": "xAI Grok Family",
}

KNOWN_IMPORTED_TYPES = {"chat", "embed", "vision", "reasoning", "coder", "image", "audio"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def format_short_date(iso_value: str) -> str:
    parsed = date.fromisoformat(iso_value)
    return f"{parsed.day} {parsed.strftime('%b')} {parsed.year}"


def format_long_date(iso_value: str) -> str:
    parsed = date.fromisoformat(iso_value)
    return f"{parsed.day} {parsed.strftime('%B')} {parsed.year}"


def extract_single(pattern: str, text: str, label: str) -> str | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return None
    return match.group(1)


def extract_stats(html: str) -> dict[str, int]:
    pairs = re.findall(
        r'<div class="stat"><div class="stat-num">(\d+)</div><div class="stat-label">([^<]+)</div></div>',
        html,
    )
    return {label.strip(): int(value) for value, label in pairs}


def extract_scope_counts(html: str) -> tuple[int, int, int] | None:
    hosted = re.search(r'id="hostedScopeCount">(\d+) active / (\d+)</span>', html)
    imported = re.search(r'id="importedScopeCount">(\d+)</span>', html)
    if not hosted or not imported:
        return None
    return int(hosted.group(1)), int(hosted.group(2)), int(imported.group(1))


def extract_deployment_counts(html: str) -> tuple[int, int, int, int, int, int] | None:
    patterns = (
        r'id="anyDeploymentCount">(\d+) / (\d+)</span>',
        r'id="ondemandDeploymentCount">(\d+) / (\d+)</span>',
        r'id="dedicatedDeploymentCount">(\d+) / (\d+)</span>',
    )
    matches = [re.search(pattern, html) for pattern in patterns]
    if not all(matches):
        return None
    return tuple(int(value) for match in matches for value in match.groups())


def extract_import_intro_counts(html: str) -> tuple[int, int] | None:
    match = re.search(
        r"(\d+)\s+provider families\s*[^0-9<]+\s*(\d+)\s+models",
        html,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def extract_family_ids(html: str) -> list[str]:
    return re.findall(r'class="import-family-title"\s+data-family="([^"]+)"', html)


def audit(repo: Path) -> int:
    index_path = repo / "index.html"
    models_path = repo / "models.json"
    imported_path = repo / "imported-models.json"
    html = read_text(index_path)
    models = read_json(models_path)
    imported = read_json(imported_path)

    chat_models = models["chatModels"]
    embedding_models = models["embeddingModels"]
    rerank_models = models["rerankModels"]
    providers = sorted({model["provider"] for model in chat_models})
    imported_families = imported["families"]
    imported_models = [model for family in imported_families for model in family["models"]]
    active_chat = sum(model.get("status") == "active" for model in chat_models)
    active_embedding = sum(model.get("status") == "active" for model in embedding_models)
    active_rerank = sum(model.get("status") == "active" for model in rerank_models)
    native_models = chat_models + embedding_models + rerank_models

    def supports_deployment(model: dict, deployment: str) -> bool:
        access_modes = model.get("regions", {}).values()
        return any(mode in {"both", deployment} for mode in access_modes)

    models_date = models["metadata"]["dataDate"]
    imported_date = imported["metadata"]["dataDate"]
    expected_header_date = format_short_date(models_date)
    expected_footnote_date = format_long_date(models_date)
    expected_stats = {
        "Model Providers": len(providers),
        f"Chat Models ({active_chat} Active)": len(chat_models),
        f"Embedding Models ({active_embedding} Active)": len(embedding_models),
        f"Rerank Models ({active_rerank} Active)": len(rerank_models),
        "Imported Models": len(imported_models),
    }

    header_date = extract_single(r"Updated\s+([0-9]{1,2}\s+[A-Za-z]{3}\s+[0-9]{4})", html, "header date")
    date_modified = extract_single(r'"dateModified":\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"', html, "dateModified")
    footnote_date = extract_single(
        r"last updated\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",
        html,
        "footnote date",
    )
    html_stats = extract_stats(html)
    scope_counts = extract_scope_counts(html)
    deployment_counts = extract_deployment_counts(html)
    import_intro_counts = extract_import_intro_counts(html)
    html_family_ids = extract_family_ids(html)
    json_family_ids = [family["id"] for family in imported_families]
    imported_types = sorted({model.get("type", "chat") for model in imported_models})

    errors: list[str] = []
    warnings: list[str] = []
    ok: list[str] = []

    if models_date == imported_date:
        ok.append(f"models.json and imported-models.json share dataDate {models_date}")
    else:
        warnings.append(
            "models.json dataDate "
            f"{models_date} differs from imported-models.json dataDate {imported_date}"
        )

    if header_date == expected_header_date:
        ok.append(f'header updated date matches "{expected_header_date}"')
    else:
        errors.append(
            f'header updated date is "{header_date or "missing"}", expected "{expected_header_date}"'
        )

    if date_modified == models_date:
        ok.append(f'JSON-LD dateModified matches "{models_date}"')
    else:
        errors.append(
            f'JSON-LD dateModified is "{date_modified or "missing"}", expected "{models_date}"'
        )

    if footnote_date == expected_footnote_date:
        ok.append(f'footnote data-source date matches "{expected_footnote_date}"')
    else:
        errors.append(
            f'footnote data-source date is "{footnote_date or "missing"}", expected "{expected_footnote_date}"'
        )

    if html_stats == expected_stats:
        ok.append("stat-bar counts match JSON data")
    else:
        errors.append(f"stat-bar counts are {html_stats}, expected {expected_stats}")

    expected_scope_counts = (
        active_chat + active_embedding + active_rerank,
        len(chat_models) + len(embedding_models) + len(rerank_models),
        len(imported_models),
    )
    if scope_counts == expected_scope_counts:
        ok.append("catalog scope active/total counts match JSON data")
    else:
        errors.append(
            f"catalog scope counts are {scope_counts or 'missing'}, expected {expected_scope_counts}"
        )

    ondemand_models = [model for model in native_models if supports_deployment(model, "ondemand")]
    dedicated_models = [model for model in native_models if supports_deployment(model, "dedicated")]
    expected_deployment_counts = (
        active_chat + active_embedding + active_rerank,
        len(native_models),
        sum(model.get("status") == "active" for model in ondemand_models),
        len(ondemand_models),
        sum(model.get("status") == "active" for model in dedicated_models) + len(imported_models),
        len(dedicated_models) + len(imported_models),
    )
    if deployment_counts == expected_deployment_counts:
        ok.append("deployment-path active/total counts match JSON data")
    else:
        errors.append(
            "deployment-path counts are "
            f"{deployment_counts or 'missing'}, expected {expected_deployment_counts}"
        )

    if import_intro_counts == (len(imported_families), len(imported_models)):
        ok.append("imported-model intro counts match JSON data")
    else:
        errors.append(
            "imported-model intro counts are "
            f"{import_intro_counts or 'missing'}, expected {(len(imported_families), len(imported_models))}"
        )

    if html_family_ids == json_family_ids:
        ok.append("import family mount points match imported-models.json family ids")
    else:
        errors.append(
            f"import family ids in HTML are {html_family_ids}, expected {json_family_ids}"
        )

    unsupported_providers = [provider for provider in providers if provider not in PROVIDER_SECTION_KEYWORDS]
    if unsupported_providers:
        errors.append(
            "native providers missing hardcoded section support: " + ", ".join(unsupported_providers)
        )
    else:
        ok.append("all native providers are covered by hardcoded section mappings")

    for provider in providers:
        keyword = PROVIDER_SECTION_KEYWORDS.get(provider)
        if keyword and keyword not in html:
            errors.append(f'missing section title containing "{keyword}" for provider "{provider}"')

    unknown_imported_types = [item for item in imported_types if item not in KNOWN_IMPORTED_TYPES]
    if unknown_imported_types:
        warnings.append(
            "imported-model types not covered by the current audit mapping: "
            + ", ".join(unknown_imported_types)
        )
    else:
        ok.append("all imported-model types are known to the current renderer")

    repo_codex = repo / ".codex"
    if repo_codex.exists() and repo_codex.is_file():
        warnings.append(
            "repo root contains a .codex file; replace it with a directory before adding project-local Codex config"
        )

    print(f"Repo: {repo}")
    print(
        "Counts: "
        f"providers={len(providers)}, "
        f"chat={len(chat_models)}, "
        f"embed={len(embedding_models)}, "
        f"rerank={len(rerank_models)}, "
        f"imported_families={len(imported_families)}, "
        f"imported_models={len(imported_models)}"
    )
    print(f"Data dates: models={models_date}, imported={imported_date}")

    if ok:
        print("\nOK:")
        for item in ok:
            print(f"  - {item}")

    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"  - {item}")

    if errors:
        print("\nErrors:")
        for item in errors:
            print(f"  - {item}")
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the OCI GenAI Catalog repository (default: %(default)s)",
    )
    args = parser.parse_args()
    return audit(Path(args.repo).expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
