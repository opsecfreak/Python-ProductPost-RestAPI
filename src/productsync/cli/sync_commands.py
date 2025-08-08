from __future__ import annotations
from typing import Any, Dict, List
from ..services.woocommerce_service import WooCommerceService
from ..services.openai_enrichment import OpenAIEnrichmentService
from ..data.csv_store import CSVStore
from ..config import settings
import pandas as pd

woo = WooCommerceService()
store = CSVStore()

def command_sync(pages: int = 1) -> int:
    total = 0
    for page in range(1, pages + 1):
        products = woo.fetch_products(page=page)
        if not products:
            break
        store.upsert_products(products)
        total += len(products)
        if len(products) < settings.woo_page_size:
            break
    return total


def command_enrich(product_id: int) -> Dict[str, Any]:
    df = store.load_df()
    if df.empty or product_id not in set(df['id'].astype(int)):
        raise SystemExit(f"Product {product_id} not found in CSV. Run sync first.")
    product_row = df.loc[df['id'] == product_id].iloc[0]
    product_payload = {
        'id': int(product_row['id']),
        'name': product_row['name'],
        'short_description': product_row['short_description'],
        'description': product_row['description'],
        'categories': [],  # could enrich if we stored
    }
    enricher = OpenAIEnrichmentService()
    enriched = enricher.enrich_product(product_payload)
    store.apply_enrichment(enriched)
    return enriched


def command_stats() -> Dict[str, Any]:
    return store.stats()


def command_push(limit: int = 10) -> List[int]:
    if not settings.enable_push_changes:
        raise SystemExit("Push disabled. Set ENABLE_PUSH_CHANGES=true in .env to allow.")
    df = store.load_df()
    if df.empty:
        return []
    pending = df[df['pending_push'] == True]  # noqa: E712
    to_push = pending.head(limit)
    pushed_ids: List[int] = []
    for _, row in to_push.iterrows():
        product_id = int(row['id'])
        data = {
            'name': row['title'],
            'short_description': row['short_description'],
            'description': row['description'],
        }
        woo.update_product(product_id, data)
        df.loc[df['id'] == product_id, 'pending_push'] = False
        pushed_ids.append(product_id)
    store.save_df(df)
    return pushed_ids


def command_create_product(name: str, price: str, description: str = "", short_description: str = "", images: list[str] | None = None, status: str = "draft") -> dict:
    """Create a new product in WooCommerce and add it to local CSV.

    price must be string per WooCommerce API (e.g., "19.99").
    images: list of URLs; will be mapped to [{'src': url}].
    status: 'draft' (default) or 'publish'.
    """
    payload = {
        'name': name,
        'type': 'simple',
        'regular_price': price,
        'description': description,
        'short_description': short_description,
        'status': status,
    }
    if images:
        payload['images'] = [{'src': u} for u in images]
    created = woo.create_product(payload)
    # Upsert so local CSV knows about it immediately
    store.upsert_products([created])
    return created
