from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()  # loads from .env


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y"}


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    try:
        return int(val) if val is not None else default
    except ValueError:
        return default


def _get(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    woo_base_url: str
    woo_consumer_key: str
    woo_consumer_secret: str
    woo_page_size: int

    openai_api_key: str
    openai_model: str
    openai_temperature: float
    openai_max_tokens: int

    output_csv_path: str
    csv_backup_keep: int

    title_max_len: int
    short_desc_max_len: int
    desc_max_len: int
    keywords_max_total_len: int

    enable_push_changes: bool
    log_level: str
    app_env: str
    app_name: str

    @staticmethod
    def load() -> "Settings":
        return Settings(
            woo_base_url=_get("WOO_BASE_URL", ""),
            woo_consumer_key=_get("WOO_CONSUMER_KEY", ""),
            woo_consumer_secret=_get("WOO_CONSUMER_SECRET", ""),
            woo_page_size=_get_int("WOO_PAGE_SIZE", 50),
            openai_api_key=_get("OPENAI_API_KEY", ""),
            openai_model=_get("OPENAI_MODEL", "gpt-4o-mini"),
            openai_temperature=float(_get("OPENAI_TEMPERATURE", "0.4")),
            openai_max_tokens=_get_int("OPENAI_MAX_TOKENS", 800),
            output_csv_path=_get("OUTPUT_CSV_PATH", "./data/products.csv"),
            csv_backup_keep=_get_int("CSV_BACKUP_KEEP", 3),
            title_max_len=_get_int("TITLE_MAX_LEN", 100),
            short_desc_max_len=_get_int("SHORT_DESC_MAX_LEN", 200),
            desc_max_len=_get_int("DESC_MAX_LEN", 1200),
            keywords_max_total_len=_get_int("KEYWORDS_MAX_TOTAL_LEN", 200),
            enable_push_changes=_get_bool("ENABLE_PUSH_CHANGES", False),
            log_level=_get("LOG_LEVEL", "INFO"),
            app_env=_get("APP_ENV", "development"),
            app_name=_get("APP_NAME", "ProductSyncCLI"),
        )


settings = Settings.load()
