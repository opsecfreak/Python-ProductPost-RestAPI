# Product Sync & AI Enrichment CLI

Syncs WooCommerce products to a local CSV, enriches content via OpenAI, validates results, and (optionally) pushes changes back to WooCommerce when approved.

## Features
- Fetch & merge WooCommerce products locally (id, name, descriptions, images meta)
- Maintain a versioned CSV (rotating backups)
- Enrich selected product fields using OpenAI (titles, short & long descriptions, keywords) via structured JSON prompt
- Guardrail validation (lengths, simple content checks, required fields)
- Track enrichment timestamps and mark rows as pending push
- Stats reporting (counts, images %, enrichment coverage, avg description length)
- Optional safe push-back to WooCommerce (opt-in via env flag)

## Project Structure
```
src/productsync/
	config.py                  # Settings loader from .env
	cli/
		main.py                  # Entry point (productsync)
		sync_commands.py         # Subcommand implementations
	services/
		woocommerce_service.py   # WooCommerce REST interactions
		openai_enrichment.py     # OpenAI content generation & validation
	data/
		csv_store.py             # CSV storage / backup / stats / enrichment application
	validation/
		validators.py            # Guardrail validation logic
```

## Requirements
See `requirements.txt` for pinned deps.

Install (recommended venv):
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables (.env)
Copy `.env` and fill in real secrets:
```
WOO_BASE_URL=https://yourstore.com
WOO_CONSUMER_KEY=ck_xxx
WOO_CONSUMER_SECRET=cs_xxx
OPENAI_API_KEY=sk_xxx
OPENAI_MODEL=gpt-4o-mini
OUTPUT_CSV_PATH=./data/products.csv
ENABLE_PUSH_CHANGES=False
# ... see full .env for more knobs
```

`ENABLE_PUSH_CHANGES` must be set to `true` before any push occurs.

## Usage
Run via module path or add a console script wrapper:
```bash
python -m productsync.cli.main sync --pages 2
python -m productsync.cli.main stats
python -m productsync.cli.main enrich 1234
python -m productsync.cli.main push --limit 5
```

Example flow:
1. Sync products: `python -m productsync.cli.main sync --pages 3`
2. View stats: `python -m productsync.cli.main stats`
3. Enrich a product: `python -m productsync.cli.main enrich 101`
4. Inspect CSV (`data/products.csv`) and edit manually if desired
5. Enable pushing: set `ENABLE_PUSH_CHANGES=true` in `.env`
6. Push: `python -m productsync.cli.main push --limit 5`

## CSV Columns
| Column | Purpose |
|--------|---------|
| id | WooCommerce product ID |
| name | Original name |
| title | Enriched (or initial) title |
| short_description | Enriched short description |
| description | Enriched long description |
| keywords | Comma-separated keywords |
| has_images | Boolean flag |
| image_count | Number of images |
| last_synced | Epoch of last sync for row |
| last_enriched | Epoch of enrichment (blank if none) |
| pending_push | True if local changes not yet pushed |

## Safety & Notes
- All *.env* files are gitignored.
- Backups rotate with timestamp suffix; adjust `CSV_BACKUP_KEEP` as needed.
- Validation is intentionally simple; extend in `validators.py`.
- OpenAI costs usage-based: keep token limits modest.

## Roadmap Ideas
- Batch enrichment command
- Rate limiting & retry enhancements
- Image alt-text generation
- Console script entry point in `pyproject.toml` / `setup.cfg`
- Tests (pytest) for validation & CSV store

## License
MIT (add license file if needed)

