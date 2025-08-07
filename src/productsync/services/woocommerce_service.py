from __future__ import annotations
from typing import List, Dict, Any
from woocommerce import API
from ..config import settings

class WooCommerceService:
    def __init__(self) -> None:
        self.api = API(
            url=settings.woo_base_url,
            consumer_key=settings.woo_consumer_key,
            consumer_secret=settings.woo_consumer_secret,
            version="wc/v3",
            timeout=30
        )

    def fetch_products(self, page: int = 1, per_page: int | None = None) -> List[Dict[str, Any]]:
        per_page = per_page or settings.woo_page_size
        response = self.api.get("products", params={"page": page, "per_page": per_page})
        response.raise_for_status()
        return response.json()

    def update_product(self, product_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.api.put(f"products/{product_id}", data)
        response.raise_for_status()
        return response.json()
