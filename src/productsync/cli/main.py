from __future__ import annotations
import argparse
import json
from .sync_commands import command_sync, command_enrich, command_stats, command_push

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="productsync", description="WooCommerce Product Sync & Enrichment CLI")
    sub = p.add_subparsers(dest="command", required=True)

    s_sync = sub.add_parser("sync", help="Fetch products from WooCommerce and merge into local CSV")
    s_sync.add_argument('--pages', type=int, default=1, help='Number of pages to fetch')

    s_enrich = sub.add_parser("enrich", help="Enrich a product by ID (AI generated content)")
    s_enrich.add_argument('product_id', type=int)

    s_stats = sub.add_parser("stats", help="Show CSV statistics")

    s_push = sub.add_parser("push", help="Push pending enriched changes back to WooCommerce (requires ENABLE_PUSH_CHANGES=true)")
    s_push.add_argument('--limit', type=int, default=10, help='Max products to push in this run')

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == 'sync':
        res = command_sync(pages=args.pages)
        print(json.dumps({'synced': res}, indent=2))
    elif args.command == 'enrich':
        res = command_enrich(product_id=args.product_id)
        print(json.dumps(res, indent=2))
    elif args.command == 'stats':
        res = command_stats()
        print(json.dumps(res, indent=2))
    elif args.command == 'push':
        res = command_push(limit=args.limit)
        print(json.dumps({'pushed': res}, indent=2))

if __name__ == '__main__':  # pragma: no cover
    main()
