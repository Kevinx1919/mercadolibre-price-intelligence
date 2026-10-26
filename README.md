# Mercado Libre Price Intelligence

End-to-end data engineering portfolio project that tracks laptop prices in
Mercado Libre Colombia (`MCO`). It demonstrates reliable ingestion, lakehouse
modeling, data quality, orchestration, AI-assisted governance, and business
analytics — not only a dashboard.

## Business objective

The project will answer these questions with historical listing data:

- How are laptop prices changing over time?
- Which sellers have the highest published stock?
- What discount exists between original and current listing prices?
- How do new and used listings differ by price and discount?

## Architecture

```text
Mercado Libre public API
          |
Python extraction with retries
          |
Unity Catalog Volume: raw_marketplace
          |
Bronze Delta -> Silver Delta -> Gold Delta -> Power BI
          |
n8n + Ollama: schema-drift review only
```

The AI workflow is advisory and auditable. It must never replace deterministic
PySpark transformations or automatically alter production data.

## Databricks assets

The Databricks workspace currently contains:

```text
Catalog: workspace
Schema: meli_price_intelligence
Volume: raw_marketplace
```

A Volume stores landing files such as raw JSON. The pipeline will create Delta
tables in `workspace.meli_price_intelligence`; those governed tables become the
Bronze, Silver, and Gold lakehouse layers.

## Roadmap

### Phase 1 — Raw ingestion: in progress

- [x] Create repository and Databricks workspace, schema, Volume, and smoke test.
- [x] Add local extraction with retries and a run manifest.
- [ ] Execute the first real extraction and upload its raw JSON to the Volume.
- [ ] Create the `bronze_api_payloads` Delta table.

### Phase 2 — Reliable transformations

- [ ] Create Silver parsing for listings, sellers, prices, and attributes.
- [ ] Add data-quality rules and a quarantine table.
- [ ] Create Gold price snapshots, seller dimension, and business aggregates.
- [ ] Add unit tests with fixtures and idempotency checks.

### Phase 3 — Operations and governance

- [ ] Run the pipeline every six hours in `America/Bogota` with Databricks Jobs.
- [ ] Add GitHub Actions validation, freshness checks, and run metadata.
- [ ] Build an n8n + Ollama workflow that reviews schema drift without write
      permission over data or pipeline code.

### Phase 4 — Analytics and portfolio delivery

- [ ] Connect Power BI to Gold through Databricks SQL.
- [ ] Build price trend, discount, condition, and seller-stock metrics.
- [ ] Publish architecture documentation, a runbook, test evidence, and demo.

## Current stage: raw extraction

The first component retrieves one API search page and stores two local files:

- An unchanged JSON response: the future lakehouse raw input.
- A manifest with the run ID, timestamp, parameters, result count, and SHA-256 hash.

Raw responses are deliberately ignored by Git. They are execution data and will
be uploaded to the `raw_marketplace` Unity Catalog Volume before Bronze ingestion.

### Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src\extract_marketplace.py
```

The default request searches `laptop` in Colombia and retrieves up to 50 items.
For another query:

```powershell
python src\extract_marketplace.py --query "laptop lenovo" --limit 25
```

After a successful execution, upload only the generated `.json` raw payload to:

```text
/Volumes/workspace/meli_price_intelligence/raw_marketplace/landing/
```

Keep the matching `.manifest.json` locally for now; it will become the run audit
metadata when we automate the ingestion.

## Technology choices

| Responsibility | Technology |
| --- | --- |
| Source | Mercado Libre public REST API |
| Extraction | Python + `requests` |
| Lakehouse | Databricks, PySpark, Delta Lake, Unity Catalog |
| Scheduling | Databricks Jobs every six hours |
| AI governance | n8n + Ollama |
| Business intelligence | Power BI + Databricks SQL |
| Version control and CI/CD | GitHub + GitHub Actions |

## Guiding principles

- Preserve source data before transforming it.
- Make every run observable, repeatable, and idempotent.
- Keep AI advisory; deterministic code owns transformations.
- Prefer a small, working pipeline over untested platform integrations.
