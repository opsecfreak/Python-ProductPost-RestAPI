from __future__ import annotations
from typing import Dict, Any
import json
import time
import openai
from ..config import settings
from ..validation.validators import EnrichmentValidator

PROMPT_TEMPLATE = """
You are an assistant that generates SEO-friendly product content. Return ONLY a compact JSON object with keys: title, short_description, description, keywords (comma-separated string). Avoid markdown. Keep within length limits: title <= {title_max}, short_description <= {short_max}, description <= {desc_max}, keywords total length <= {kw_max}. Product data: {product_data}
""".strip()

class OpenAIEnrichmentService:
    def __init__(self) -> None:
        openai.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.validator = EnrichmentValidator(
            title_max=settings.title_max_len,
            short_desc_max=settings.short_desc_max_len,
            desc_max=settings.desc_max_len,
            keywords_max_total=settings.keywords_max_total_len,
        )

    def enrich_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "id": product.get("id"),
            "name": product.get("name"),
            "short_description": product.get("short_description"),
            "description": product.get("description"),
            "categories": [c.get("name") for c in product.get("categories", [])],
        }
        prompt = PROMPT_TEMPLATE.format(
            title_max=settings.title_max_len,
            short_max=settings.short_desc_max_len,
            desc_max=settings.desc_max_len,
            kw_max=settings.keywords_max_total_len,
            product_data=json.dumps(payload, ensure_ascii=False),
        )
        # Basic retry with backoff
        for attempt in range(3):
            try:
                completion = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=float(settings.openai_temperature),
                    max_tokens=settings.openai_max_tokens,
                    response_format={"type": "json_object"}
                )
                raw_content = completion.choices[0].message.content
                data = json.loads(raw_content)
                valid = self.validator.validate(data)
                if not valid.ok:
                    raise ValueError(f"Validation failed: {valid.errors}")
                data["_validated"] = True
                return data
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)
        raise RuntimeError("Enrichment failed after retries")
