#!/usr/bin/env python3
"""
Visapolicy.ai — Phase 1 Pipeline Runner

Usage:
  python run.py                  # process last 7 days
  python run.py --days 14        # process last 14 days
  python run.py --dry-run        # extract only, skip emails
"""
import asyncio
import argparse
from loguru import logger
from src.pipeline import Pipeline


async def main() -> None:
    parser = argparse.ArgumentParser(description="Visapolicy.ai Phase 1 Pipeline")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="Extract changes but do not send emails")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN — no emails will be sent")

    pipeline = Pipeline(dry_run=args.dry_run)
    stats = await pipeline.run(lookback_days=args.days)

    print("\n" + "=" * 50)
    print("Pipeline Summary")
    print("=" * 50)
    for key, val in stats.items():
        print(f"  {key.replace('_', ' ').title():<28} {val}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
