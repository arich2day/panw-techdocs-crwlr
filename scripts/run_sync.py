#!/usr/bin/env python3
"""
SyncLM Studio CLI: Standalone Documentation Ingestion & Sync Runner.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from engine.pipeline import SyncPipeline, PipelineEvent
from engine.sources import TECHNOLOGIES, VENDORS, DOC_TYPES

# ANSI Color codes for clean terminal output
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"


async def main_async(args):
    technologies = [args.tech] if args.tech and args.tech != "all" else None
    vendors = [args.vendor] if args.vendor and args.vendor != "all" else None
    doc_types = [args.doc_type] if args.doc_type and args.doc_type != "all" else None

    print(f"{BOLD}{CYAN}==================================================================={RESET}")
    print(f"{BOLD}{CYAN}   SyncLM Studio — TechDocs Sync Pipeline for NotebookLM           {RESET}")
    print(f"{BOLD}{CYAN}==================================================================={RESET}")
    print(f" * Technology Filter : {args.tech or 'all'}")
    print(f" * Vendor Filter     : {args.vendor or 'all'}")
    print(f" * Doc Type Filter   : {args.doc_type or 'all'}")
    print(f" * Mode              : {'DRY RUN (Simulation)' if args.dry_run else 'LIVE Google Docs Sync'}")
    print(f" * Concurrency       : {args.concurrency}")
    print(f"-------------------------------------------------------------------")

    queue = asyncio.Queue()
    pipeline = SyncPipeline(event_queue=queue, dry_run=args.dry_run, concurrency=args.concurrency)

    async def log_consumer():
        while True:
            event: PipelineEvent = await queue.get()
            color = CYAN
            if event.level == "SUCCESS":
                color = GREEN
            elif event.level == "WARN":
                color = YELLOW
            elif event.level == "ERROR":
                color = RED

            print(f"{color}[{event.timestamp}] [{event.level}] {event.message}{RESET}")
            queue.task_done()
            if event.event_type == "complete":
                break

    consumer_task = asyncio.create_task(log_consumer())

    summary = await pipeline.run(
        technologies=technologies,
        vendors=vendors,
        doc_types=doc_types,
        dry_run=args.dry_run
    )

    await consumer_task

    print(f"{BOLD}{CYAN}==================================================================={RESET}")
    print(f"{GREEN}Pipeline execution finished.{RESET}")
    print(f"Sources Updated: {summary.get('updated', 0)} | Cached: {summary.get('cached', 0)} | Failed: {summary.get('failed', 0)}")
    print(f"Google Docs Synced: {summary.get('synced_targets', 0)}")
    print(f"Duration: {summary.get('duration_seconds', 0)}s")
    print(f"{BOLD}{CYAN}==================================================================={RESET}")


def main():
    parser = argparse.ArgumentParser(description="SyncLM Studio Documentation Ingestion CLI")
    parser.add_argument(
        "--tech", "--technology",
        dest="tech",
        choices=["all", "sase", "browser", "ngfw", "secops", "cloud"],
        default="all",
        help="Technology vertical to scrape"
    )
    parser.add_argument(
        "--vendor",
        choices=["all", "panw", "zscaler", "netskope", "island", "cloudflare", "fortinet"],
        default="all",
        help="Vendor filter"
    )
    parser.add_argument(
        "--doc-type",
        choices=["all", "architecture", "release_notes", "api_specs", "battlecards"],
        default="all",
        help="Content type filter"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Simulate scraping and normalization without writing to Google Docs"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Maximum concurrent HTTP connections"
    )

    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
