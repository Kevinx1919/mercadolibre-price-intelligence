# Mercado Libre Price Intelligence

Lakehouse project that tracks laptop prices in Mercado Libre Colombia (`MCO`).

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
