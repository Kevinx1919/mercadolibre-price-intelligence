"""Extract a raw Mercado Libre search response for the price-intelligence lakehouse.

This module intentionally preserves the API response unchanged. Parsing and
business transformations belong to the Bronze and Silver stages in Databricks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests


API_BASE_URL = "https://api.mercadolibre.com"
MAX_PAGE_SIZE = 50
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class MercadoLibreExtractionError(RuntimeError):
    """Raised when a Mercado Libre response cannot be safely persisted."""


def fetch_search_page(
    *,
    site_id: str,
    query: str,
    limit: int,
    offset: int,
    timeout_seconds: int,
    max_retries: int,
) -> tuple[dict[str, Any], str]:
    """Fetch one search page and return its JSON payload plus the final URL."""
    if not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError(f"limit must be between 1 and {MAX_PAGE_SIZE}")
    if offset < 0:
        raise ValueError("offset must be zero or greater")

    url = f"{API_BASE_URL}/sites/{site_id}/search"
    params = {"q": query, "limit": limit, "offset": offset}
    headers = {"User-Agent": "mercadolibre-price-intelligence/0.1"}

    with requests.Session() as session:
        for attempt in range(max_retries + 1):
            try:
                response = session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout_seconds,
                )
            except requests.RequestException as error:
                if attempt == max_retries:
                    raise MercadoLibreExtractionError(
                        f"Network error after {attempt + 1} attempts: {error}"
                    ) from error
                time.sleep(2**attempt)
                continue

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < max_retries:
                retry_after = response.headers.get("Retry-After")
                delay = int(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
                time.sleep(delay)
                continue

            try:
                response.raise_for_status()
                payload = response.json()
            except (requests.HTTPError, ValueError) as error:
                body_preview = response.text[:300]
                raise MercadoLibreExtractionError(
                    f"Mercado Libre returned HTTP {response.status_code}: {body_preview}"
                ) from error

            if not isinstance(payload, dict):
                raise MercadoLibreExtractionError("Expected a JSON object from Mercado Libre")
            return payload, response.url

    raise AssertionError("Unreachable retry loop")


def write_raw_run(
    *,
    payload: dict[str, Any],
    output_dir: Path,
    site_id: str,
    query: str,
    limit: int,
    offset: int,
    request_url: str,
) -> tuple[Path, Path]:
    """Persist an immutable raw payload and a separate ingestion manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_at = datetime.now(UTC)
    run_id = str(uuid.uuid4())
    timestamp = extracted_at.strftime("%Y%m%dT%H%M%SZ")
    query_slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-") or "search"
    stem = f"{site_id.lower()}_{query_slug}_{timestamp}_{run_id[:8]}"

    raw_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    raw_path = output_dir / f"{stem}.json"
    manifest_path = output_dir / f"{stem}.manifest.json"
    raw_path.write_bytes(raw_bytes)

    manifest = {
        "run_id": run_id,
        "extracted_at_utc": extracted_at.isoformat(),
        "source_name": "mercado_libre_search",
        "request_url": request_url,
        "request_parameters": {
            "site_id": site_id,
            "query": query,
            "limit": limit,
            "offset": offset,
        },
        "raw_file": raw_path.name,
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "returned_results": len(payload.get("results", [])),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return raw_path, manifest_path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract one Mercado Libre search page as raw JSON.")
    parser.add_argument("--site-id", default="MCO", help="Mercado Libre site identifier (default: MCO)")
    parser.add_argument("--query", default="laptop", help="Search text (default: laptop)")
    parser.add_argument("--limit", type=int, default=50, help="Items to request, from 1 to 50")
    parser.add_argument("--offset", type=int, default=0, help="Pagination offset (default: 0)")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=3, help="Retries for temporary failures")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    payload, request_url = fetch_search_page(
        site_id=args.site_id,
        query=args.query,
        limit=args.limit,
        offset=args.offset,
        timeout_seconds=args.timeout,
        max_retries=args.max_retries,
    )
    raw_path, manifest_path = write_raw_run(
        payload=payload,
        output_dir=args.output_dir,
        site_id=args.site_id,
        query=args.query,
        limit=args.limit,
        offset=args.offset,
        request_url=request_url,
    )
    print(f"Raw payload: {raw_path}")
    print(f"Run manifest: {manifest_path}")


if __name__ == "__main__":
    main()
