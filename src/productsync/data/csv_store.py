from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import shutil
import time
from ..config import settings

COLUMNS = [
    "id", "name", "title", "short_description", "description", "keywords",
    "has_images", "image_count", "last_synced", "last_enriched", "pending_push"
]

class CSVStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or settings.output_csv_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _rotate_backups(self) -> None:
        if not self.path.exists():
            return
        timestamp = int(time.time())
        backup = self.path.with_suffix(f".bak.{timestamp}.csv")
        shutil.copy2(self.path, backup)
        backups = sorted(self.path.parent.glob(self.path.name + ".bak.*.csv"), reverse=True)
        for old in backups[settings.csv_backup_keep:]:
            old.unlink(missing_ok=True)

    def load_df(self) -> pd.DataFrame:
        if self.path.exists():
            return pd.read_csv(self.path)
        return pd.DataFrame(columns=COLUMNS)

    def save_df(self, df: pd.DataFrame) -> None:
        df.to_csv(self.path, index=False)

    def upsert_products(self, products: List[Dict[str, Any]]) -> None:
        df = self.load_df()
        existing_ids = set(df['id'].astype(int)) if not df.empty else set()
        new_rows = []
        for p in products:
            pid = p.get('id')
            name = p.get('name')
            images = p.get('images', []) or []
            has_images = bool(images)
            image_count = len(images)
            row = {
                'id': pid,
                'name': name,
                'title': name,  # initial title
                'short_description': p.get('short_description', ''),
                'description': p.get('description', ''),
                'keywords': '',
                'has_images': has_images,
                'image_count': image_count,
                'last_synced': int(time.time()),
                'last_enriched': '',
                'pending_push': False,
            }
            if pid in existing_ids:
                # update some fields
                df.loc[df['id'] == pid, ['name', 'has_images', 'image_count', 'last_synced']] = [
                    row['name'], row['has_images'], row['image_count'], row['last_synced']
                ]
            else:
                new_rows.append(row)
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        self._rotate_backups()
        self.save_df(df)

    def apply_enrichment(self, enriched: Dict[str, Any]) -> None:
        df = self.load_df()
        pid = enriched.get('id')
        if df.empty or pid not in set(df['id'].astype(int)):
            raise ValueError(f"Product id {pid} not present in CSV")
        df.loc[df['id'] == pid, [
            'title', 'short_description', 'description', 'keywords', 'last_enriched', 'pending_push'
        ]] = [
            enriched.get('title', ''),
            enriched.get('short_description', ''),
            enriched.get('description', ''),
            enriched.get('keywords', ''),
            int(time.time()),
            True,
        ]
        self._rotate_backups()
        self.save_df(df)

    def stats(self) -> Dict[str, Any]:
        df = self.load_df()
        if df.empty:
            return {"count": 0}
        with_images = int(df['has_images'].sum())
        avg_desc_len = int(df['description'].fillna('').str.len().mean()) if not df['description'].empty else 0
        enriched = int((df['last_enriched'] != '').sum())
        pending = int(df['pending_push'].sum())
        return {
            'count': int(len(df)),
            'with_images': with_images,
            'with_images_pct': round(with_images / len(df) * 100, 1) if len(df) else 0,
            'avg_description_length': avg_desc_len,
            'enriched_count': enriched,
            'enriched_pct': round(enriched / len(df) * 100, 1) if len(df) else 0,
            'pending_push': pending,
        }
