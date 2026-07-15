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
    catalog_path = repo / "catalog.json"
    legacy_paths = [repo / "models.json", repo / "imported-models.json"]
    html = read_text(index_path)
    catalog = read_json(catalog_path)
    models = catalog["pretrained"]
    imported = catalog["imported"]

    chat_models = models["chatModels"]
    embedding_models = models["embeddingModels"]
    rerank_models = models["rerankModels"]
    operational_models = models["operationalModels"]
    operational_ids = [model["id"] for model in operational_models]
    presentation_ids = [
        model["id"] for model in chat_models + embedding_models + rerank_models
    ]
    providers = sorted({model["provider"] for model in chat_models})
    imported_families = imported["families"]
    imported_models = [model for family in imported_families for model in family["models"]]
    catalog_date = catalog["metadata"]["dataDate"]
    expected_header_date = format_short_date(catalog_date)
    expected_footnote_date = format_long_date(catalog_date)
    header_date = extract_single(r"Updated\s+([0-9]{1,2}\s+[A-Za-z]{3}\s+[0-9]{4})", html, "header date")
    date_modified = extract_single(r'"dateModified":\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"', html, "dateModified")
    footnote_date = extract_single(
        r"last updated\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",
        html,
        "footnote date",
    )
    import_intro_counts = extract_import_intro_counts(html)
    html_family_ids = extract_family_ids(html)
    json_family_ids = [family["id"] for family in imported_families]
    imported_types = sorted({model.get("type", "chat") for model in imported_models})

    errors: list[str] = []
    warnings: list[str] = []
    ok: list[str] = []

    if "native" in catalog or "native" in catalog["metadata"]["sources"]:
        errors.append("obsolete native-model taxonomy remains in catalog.json")
    else:
        ok.append("catalog uses OCI pretrained/imported model taxonomy")

    legacy_files = [path.name for path in legacy_paths if path.exists()]
    if legacy_files:
        errors.append("legacy runtime snapshots still present: " + ", ".join(legacy_files))
    elif "fetch('catalog.json')" in html and "fetch('models.json')" not in html and "fetch('imported-models.json')" not in html:
        ok.append("page fetches catalog.json as its only runtime data source")
    else:
        errors.append("page does not exclusively fetch catalog.json")

    ok.append(f"catalog.json dataDate is {catalog_date}")

    primary_source = catalog["metadata"]["sources"]["pretrained"]["primary"]
    scan_date = primary_source["generatedAt"].split("T", maxsplit=1)[0]
    if scan_date == catalog_date:
        ok.append("catalog dataDate matches the authenticated OCI CLI scan date")
    else:
        errors.append(f"catalog dataDate {catalog_date} differs from CLI scan date {scan_date}")

    if primary_source["observedUniqueModels"] == len(operational_models):
        ok.append(f"operational inventory contains {len(operational_models)} CLI-observed model ids")
    else:
        errors.append(
            "pretrained source metadata reports "
            f"{primary_source['observedUniqueModels']} models, found {len(operational_models)}"
        )

    duplicate_operational_ids = sorted(
        {model_id for model_id in operational_ids if operational_ids.count(model_id) > 1}
    )
    if duplicate_operational_ids:
        errors.append("duplicate operational model ids: " + ", ".join(duplicate_operational_ids))
    else:
        ok.append("operational model ids are unique")

    missing_operational_ids = sorted(set(presentation_ids) - set(operational_ids))
    if missing_operational_ids:
        errors.append(
            "documentation-enriched pretrained rows not observed by OCI CLI: "
            + ", ".join(missing_operational_ids)
        )
    else:
        ok.append("all documentation-enriched pretrained rows are backed by OCI CLI observations")

    if "renderOperational(catalog.pretrained)" in html and "operationalInventoryBody" in html:
        ok.append("page renders the canonical OCI CLI operational inventory")
    else:
        errors.append("page does not render the canonical OCI CLI operational inventory")

    if header_date == expected_header_date:
        ok.append(f'header updated date matches "{expected_header_date}"')
    else:
        errors.append(
            f'header updated date is "{header_date or "missing"}", expected "{expected_header_date}"'
        )

    if date_modified == catalog_date:
        ok.append(f'JSON-LD dateModified matches "{catalog_date}"')
    else:
        errors.append(
            f'JSON-LD dateModified is "{date_modified or "missing"}", expected "{catalog_date}"'
        )

    if footnote_date == expected_footnote_date:
        ok.append(f'footnote data-source date matches "{expected_footnote_date}"')
    else:
        errors.append(
            f'footnote data-source date is "{footnote_date or "missing"}", expected "{expected_footnote_date}"'
        )

    if import_intro_counts == (len(imported_families), len(imported_models)):
        ok.append("imported-model intro counts match catalog.json data")
    else:
        errors.append(
            "imported-model intro counts are "
            f"{import_intro_counts or 'missing'}, expected {(len(imported_families), len(imported_models))}"
        )

    if html_family_ids == json_family_ids:
        ok.append("import family mount points match catalog.json imported family ids")
    else:
        errors.append(
            f"import family ids in HTML are {html_family_ids}, expected {json_family_ids}"
        )

    unsupported_providers = [provider for provider in providers if provider not in PROVIDER_SECTION_KEYWORDS]
    if unsupported_providers:
        errors.append(
            "pretrained providers missing hardcoded section support: " + ", ".join(unsupported_providers)
        )
    else:
        ok.append("all pretrained providers are covered by hardcoded section mappings")

    imported_without_cluster_options = [
        model["hfId"]
        for model in imported_models
        if not model.get("dedicatedClusterOptions")
    ]
    if imported_without_cluster_options:
        errors.append(
            "imported models without structured dedicated cluster options: "
            + ", ".join(imported_without_cluster_options)
        )
    else:
        ok.append("all imported models have structured shape and GPU options")

    invalid_cluster_options = [
        model["hfId"]
        for model in imported_models
        for option in model.get("dedicatedClusterOptions", [])
        if not option.get("unitShape")
        or not option.get("gpuType")
        or not isinstance(option.get("gpuCount"), int)
        or option["gpuCount"] < 1
        or option.get("requiredUnits") != option.get("gpuCount")
        or not option.get("limitName")
    ]
    if invalid_cluster_options:
        errors.append(
            "invalid imported shape/GPU options: " + ", ".join(sorted(set(invalid_cluster_options)))
        )
    else:
        ok.append("imported shape options have explicit GPU counts and Limits dimensions")

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
        f"operational={len(operational_models)}, "
        f"chat={len(chat_models)}, "
        f"embed={len(embedding_models)}, "
        f"rerank={len(rerank_models)}, "
        f"imported_families={len(imported_families)}, "
        f"imported_models={len(imported_models)}"
    )
    print(f"Data date: catalog={catalog_date}")

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
