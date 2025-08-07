# Product Sync & AI Enrichment CLI
<div align="center">

# Product Sync & AI Enrichment CLI

Sync WooCommerce products to a local CSV, generate SEO‑friendly content with OpenAI, validate & review locally, then (optionally) push changes back to your store safely.

</div>

---

## 1. What This Tool Does
| Stage | Purpose | Source / Target |
|-------|---------|-----------------|
| Sync  | Pull products via WooCommerce REST API | WooCommerce → Local CSV |
| Enrich | Generate improved title/descriptions/keywords | OpenAI → CSV row update |
| Validate | Length + simple content guardrails | In‑memory before commit |
| Review | Human review / manual edits | Local CSV |
| Push (opt‑in) | Apply enriched changes back to store | CSV → WooCommerce |

You always keep a local, versioned CSV that you can open in Excel, Numbers, or a text editor before pushing anything live.

---

## 2. Prerequisites
1. Python 3.11+ (3.12 recommended)
2. WooCommerce store with REST API enabled
3. API keys (read/write) for your WooCommerce store
4. OpenAI API key (for content generation)

### 2.1 Generate WooCommerce REST API Keys
WooCommerce Dashboard → Settings → Advanced → REST API → Add Key
1. Description: Product Sync CLI
2. User: (choose an account with product edit rights)
3. Permissions: Read/Write
4. Generate key → copy Consumer Key & Consumer Secret

### 2.2 OpenAI Key
Create / retrieve at https://platform.openai.com/ — copy the API key (`sk-...`).

---

## 3. Project Structure (Key Files)
```
src/productsync/
	cli/main.py              # Entry point (subcommands)
	cli/sync_commands.py     # Implementations for sync/enrich/stats/push
	config.py                # Loads environment variables
	services/woocommerce_service.py  # WooCommerce REST wrapper
	services/openai_enrichment.py    # OpenAI prompt + validation + retries
	data/csv_store.py        # CSV persistence, backups, stats
	validation/validators.py # Guardrail validator for AI output
```

Backups: Each save rotates a timestamped `.bak.*.csv` (keep count = `CSV_BACKUP_KEEP`).

---

## 4. Installation
```bash
git clone https://github.com/<your-org-or-user>/Python-ProductPost-RestAPI.git
cd Python-ProductPost-RestAPI
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 5. Configure Environment (.env)
Copy the provided `.env` template and edit:
```
WOO_BASE_URL=https://yourstore.com
WOO_CONSUMER_KEY=ck_************************
WOO_CONSUMER_SECRET=cs_************************
OPENAI_API_KEY=sk_************************
OPENAI_MODEL=gpt-4o-mini
OUTPUT_CSV_PATH=./data/products.csv
ENABLE_PUSH_CHANGES=False   # keep False until you are ready
WOO_PAGE_SIZE=50            # up to 100
TITLE_MAX_LEN=100
SHORT_DESC_MAX_LEN=200
DESC_MAX_LEN=1200
KEYWORDS_MAX_TOTAL_LEN=200
```
All `.env` variants are gitignored for safety.

### 5.1 Boolean & Numeric Handling
Booleans accept: `true/false`, `1/0`, `yes/no` (case‑insensitive).

---

## 6. Commands Overview
Run via Python module (keeps repo simple):
```bash
python -m productsync.cli.main <command> [options]
```

| Command | Purpose | Key Options |
|---------|---------|-------------|
| sync    | Fetch products into CSV | `--pages N` (default 1) |
| stats   | Show dataset statistics | — |
| enrich  | Enrich a single product by ID | `<product_id>` |
| push    | Push pending enriched rows back | `--limit N` |

### 6.1 Sync Products
```bash
python -m productsync.cli.main sync --pages 3
```
Fetches up to 3 pages (`WOO_PAGE_SIZE` per page). Creates / updates `data/products.csv`.

### 6.2 View Stats
```bash
python -m productsync.cli.main stats
```
Outputs JSON summary: total count, images %, enrichment coverage, etc.

### 6.3 Enrich a Product
```bash
python -m productsync.cli.main enrich 1234
```
Prompts OpenAI with structured JSON request & validation. Updates row and flags `pending_push = True`.

### 6.4 Push Changes (Opt‑In)
```bash
# First, in .env set ENABLE_PUSH_CHANGES=True
python -m productsync.cli.main push --limit 5
```
Updates up to 5 pending products (ordered by CSV order). Resets `pending_push` to False on success.

---

## 7. Internal Data Flow
1. `woocommerce_service.fetch_products()` → GET `/wp-json/wc/v3/products`
2. Normalizes key fields & images → `csv_store.upsert_products()`
3. `enrich` loads row → crafts prompt with length constraints → OpenAI Chat Completions (`response_format=json_object`)
4. JSON parsed → `EnrichmentValidator` ensures lengths / no URLs → CSV updated with enrichment + timestamp
5. `push` (if enabled) → `woocommerce_service.update_product()` PUT `/wp-json/wc/v3/products/<id>` with enriched fields

---

## 8. CSV Schema
| Column | Description |
|--------|-------------|
| id | WooCommerce product ID |
| name | Original product name |
| title | Enriched title (initially same as name) |
| short_description | Enriched short description |
| description | Enriched long description |
| keywords | Comma‑separated keywords from AI |
| has_images | True if any images detected |
| image_count | Number of images |
| last_synced | Epoch seconds last sync for this row |
| last_enriched | Epoch seconds of enrichment (blank if none) |
| pending_push | True if changes not yet pushed |

Backups: `products.csv.bak.<timestamp>.csv` (keeps the newest `CSV_BACKUP_KEEP`).

---

## 9. Enrichment Prompt & Guardrails
Prompt enforces max lengths (title, short, description, keywords aggregate). Output must be pure JSON. Validation rejects:
- Missing title
- Any field exceeding configured max lengths
- URLs inside description (basic filter for spam / leakage)

Extend rules in `validation/validators.py` (e.g., profanity filtering, HTML sanitization).

---

## 10. Safety Mechanisms
| Mechanism | Purpose |
|-----------|---------|
| `ENABLE_PUSH_CHANGES` flag | Prevent accidental live edits |
| CSV backups | Recovery if something unwanted overwrites content |
| Length validation | Avoid overly long / truncated store fields |
| Single-ID enrich | Review each change before pushing |
| Pending flag | Track which rows need pushing |

---

## 11. Example Full Workflow
```bash
# 1. Install & configure .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Initial sync
python -m productsync.cli.main sync --pages 5

# 3. Review CSV (open in your editor / spreadsheet)
open data/products.csv   # macOS example; use xdg-open or your editor

# 4. Enrich one product
python -m productsync.cli.main enrich 101

# 5. Repeat enrich for selected products
python -m productsync.cli.main enrich 202

# 6. Stats
python -m productsync.cli.main stats

# 7. Enable pushing (edit .env)


# 8. Push a few changes
python -m productsync.cli.main push --limit 3
```

---

## 12. Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| 401 / 403 from WooCommerce | Bad keys / permissions | Regenerate keys, ensure Read/Write |
| Empty sync results | No products or wrong base URL | Check `WOO_BASE_URL` (no trailing slash) |
| OpenAI errors / 401 | Invalid or missing `OPENAI_API_KEY` | Update .env and restart shell |
| Validation failed (length) | Model exceeded limits | Adjust max lengths or tweak model/temperature |
| Push disabled error | Flag still false | Set `ENABLE_PUSH_CHANGES=True` |

Enable verbose logging by temporarily setting `LOG_LEVEL=DEBUG` (if extended later).

---

## 13. FAQ
**Q: Can I batch enrich everything automatically?**  
Currently single-product focus for safety. You can script a loop around `enrich` (future batch command planned).

**Q: Does it overwrite my manual edits?**  
Sync updates only non-enriched metadata fields (images, name) & adds new rows; enriched fields you adjust persist unless you re-enrich.

**Q: How are HTML tags handled?**  
Prompt does not request HTML; add sanitization if you allow formatting.

**Q: Can I add alt text generation?**  
Yes—extend the OpenAI prompt & add a new CSV column.

---

## 14. Contributing
PRs welcome: add tests, batch enrich, improved validation, better logging, rate limiting. Please keep changes modular.

---

## 15. License
MIT (add LICENSE file for clarity)

---

## 16. Disclaimer
Use responsibly. Review AI‑generated content for accuracy, brand tone, and policy compliance before publishing.

