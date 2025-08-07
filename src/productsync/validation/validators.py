from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ValidationResult:
    ok: bool
    errors: List[str]

class EnrichmentValidator:
    def __init__(self, title_max: int, short_desc_max: int, desc_max: int, keywords_max_total: int) -> None:
        self.title_max = title_max
        self.short_desc_max = short_desc_max
        self.desc_max = desc_max
        self.keywords_max_total = keywords_max_total

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        title = (data.get('title') or '').strip()
        short_desc = (data.get('short_description') or '').strip()
        desc = (data.get('description') or '').strip()
        keywords = (data.get('keywords') or '').strip()

        if not title:
            errors.append('title missing')
        if len(title) > self.title_max:
            errors.append('title too long')
        if len(short_desc) > self.short_desc_max:
            errors.append('short_description too long')
        if len(desc) > self.desc_max:
            errors.append('description too long')
        if len(keywords) > self.keywords_max_total:
            errors.append('keywords total length too long')
        if any(bad in desc.lower() for bad in ["http://", "https://"]):
            errors.append('description contains URL')

        return ValidationResult(ok=not errors, errors=errors)
