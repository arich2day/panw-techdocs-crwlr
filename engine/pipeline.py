"""
SyncLM Pipeline Orchestrator.
Coordinates scraping, normalization, deduplication, and Google Docs synchronization.
Publishes real-time telemetry events to an async queue for SSE log streaming.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, AsyncGenerator
import httpx

from engine.sources import (
    DocSource,
    DocTarget,
    load_doc_sources,
    load_targets,
    filter_sources
)
from engine.scraper import DocScraper, ScrapeResult
from engine.normalizer import normalize_document
from engine.dedup import HashStore
from engine.gdocs import GoogleDocsClient

logger = logging.getLogger("synclm.pipeline")


class PipelineEvent:
    def __init__(
        self,
        event_type: str,  # start, log, source_scraped, doc_synced, complete, error
        message: str,
        level: str = "INFO",  # INFO, SUCCESS, WARN, ERROR
        data: Optional[Dict[str, Any]] = None
    ):
        self.timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.event_type = event_type
        self.message = message
        self.level = level
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "message": self.message,
            "level": self.level,
            "data": self.data
        }


class SyncPipeline:
    def __init__(
        self,
        event_queue: Optional[asyncio.Queue] = None,
        dry_run: bool = False,
        concurrency: int = 4
    ):
        self.event_queue = event_queue or asyncio.Queue()
        self.dry_run = dry_run
        self.scraper = DocScraper(concurrency=concurrency)
        self.hash_store = HashStore()
        self.gdocs_client = GoogleDocsClient()

    async def emit(self, event_type: str, message: str, level: str = "INFO", data: Optional[Dict[str, Any]] = None):
        event = PipelineEvent(event_type, message, level, data)
        await self.event_queue.put(event)
        logger.info(f"[{level}] {message}")

    async def run(
        self,
        technologies: Optional[List[str]] = None,
        vendors: Optional[List[str]] = None,
        doc_types: Optional[List[str]] = None,
        selected_source_ids: Optional[List[str]] = None,
        dry_run: Optional[bool] = None
    ) -> Dict[str, Any]:
        effective_dry_run = self.dry_run if dry_run is None else dry_run
        start_time = datetime.now(timezone.utc)

        await self.emit(
            "start",
            f"Initializing SyncLM Studio pipeline (Dry Run: {effective_dry_run})",
            level="INFO",
            data={"dry_run": effective_dry_run}
        )

        # 1. Load and filter sources
        all_sources = load_doc_sources()
        if selected_source_ids:
            id_set = set(selected_source_ids)
            sources = [s for s in all_sources if s.id in id_set]
        else:
            sources = filter_sources(
                all_sources,
                technologies=technologies,
                vendors=vendors,
                doc_types=doc_types
            )

        if not sources:
            await self.emit("warn", "No documentation sources matched the current selection filter.", level="WARN")
            return {"status": "empty", "scraped": 0, "synced": 0}

        await self.emit(
            "log",
            f"Selected {len(sources)} source target(s) across selected verticals/vendors.",
            level="INFO"
        )

        # 2. Scrape each source concurrently
        scraped_docs: Dict[str, Dict[str, Any]] = {}
        cached_count = 0
        updated_count = 0
        failed_count = 0

        async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
            tasks = []
            for source in sources:
                tasks.append(self._process_single_source(client, source))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    failed_count += 1
                    await self.emit("error", f"Pipeline worker error: {res}", level="ERROR")
                elif res:
                    source_id = res["source_id"]
                    if res["status"] == "cached":
                        cached_count += 1
                    elif res["status"] == "updated":
                        updated_count += 1
                        scraped_docs[source_id] = res
                    else:
                        failed_count += 1

        # 3. Group updated docs by technology target Google Doc
        targets = load_targets()
        target_map = {t.technology: t for t in targets}
        default_target = targets[0] if targets else None

        grouped_by_target: Dict[str, List[Dict[str, Any]]] = {}
        for s_id, doc_info in scraped_docs.items():
            tech = doc_info["technology"]
            target = target_map.get(tech, default_target)
            target_id = target.google_doc_id if target else "DEFAULT_DOC"
            if target_id not in grouped_by_target:
                grouped_by_target[target_id] = []
            grouped_by_target[target_id].append(doc_info)

        # 4. Sync grouped docs to Google Docs
        synced_targets = 0
        total_chars_synced = 0

        for doc_id, doc_list in grouped_by_target.items():
            combined_markdown = "\n\n\n".join(d["normalized_content"] for d in doc_list)
            target_tech = doc_list[0]["technology"]

            await self.emit(
                "log",
                f"Syncing {len(doc_list)} document(s) into Google Doc target [{target_tech.upper()}] (ID: {doc_id})...",
                level="INFO"
            )

            sync_res = self.gdocs_client.sync_markdown_to_doc(
                doc_id=doc_id,
                content=combined_markdown,
                dry_run=effective_dry_run
            )

            if sync_res.get("success"):
                synced_targets += 1
                chars = sync_res.get("chars_synced", 0)
                total_chars_synced += chars
                msg = sync_res.get("message") or f"Successfully synced {chars:,} chars to Google Doc '{doc_id}'."
                await self.emit("doc_synced", msg, level="SUCCESS", data=sync_res)
            else:
                err_msg = sync_res.get("error", "Unknown Google Docs sync failure")
                await self.emit("error", f"Failed syncing to Google Doc '{doc_id}': {err_msg}", level="ERROR")

        # 5. Emit summary
        duration = round((datetime.now(timezone.utc) - start_time).total_seconds(), 2)
        summary = {
            "total_sources": len(sources),
            "updated": updated_count,
            "cached": cached_count,
            "failed": failed_count,
            "synced_targets": synced_targets,
            "total_chars_synced": total_chars_synced,
            "duration_seconds": duration,
            "dry_run": effective_dry_run
        }

        await self.emit(
            "complete",
            f"Pipeline complete in {duration}s: {updated_count} updated, {cached_count} cached, {failed_count} failed. Synced {synced_targets} Google Doc target(s).",
            level="SUCCESS",
            data=summary
        )

        return summary

    async def _process_single_source(self, client: httpx.AsyncClient, source: DocSource) -> Dict[str, Any]:
        """Scrapes, normalizes, and checks hash for a single source."""
        await self.emit("log", f"Scraping [{source.vendor.upper()}] {source.title}...", level="INFO")
        
        scrape_res = await self.scraper.scrape(client, source.url, fallback_title=source.title)
        
        if not scrape_res.success:
            await self.emit(
                "error",
                f"Scrape failed for [{source.vendor.upper()}] {source.title}: {scrape_res.error}",
                level="ERROR"
            )
            return {"source_id": source.id, "status": "failed", "error": scrape_res.error}

        is_changed, new_hash, prev_hash = self.hash_store.is_changed(source.id, scrape_res.content)

        if not is_changed:
            await self.emit(
                "source_scraped",
                f"[{source.vendor.upper()}] {source.title} — Unchanged (SHA-256: {new_hash[:8]}...), skipping sync.",
                level="INFO",
                data={"status": "cached", "hash": new_hash, "source_id": source.id}
            )
            return {"source_id": source.id, "status": "cached", "hash": new_hash}

        normalized = normalize_document(
            title=scrape_res.title or source.title,
            raw_content=scrape_res.content,
            vendor=source.vendor,
            technology=source.technology,
            doc_type=source.doc_type,
            url=source.url
        )

        # Update hash store with content hash
        self.hash_store.update(source.id, scrape_res.content, source.url)
        words = len(normalized.split())

        await self.emit(
            "source_scraped",
            f"[{source.vendor.upper()}] {source.title} — Parsed {words:,} words via {scrape_res.extractor} (SHA-256: {new_hash[:8]}...).",
            level="SUCCESS",
            data={
                "status": "updated",
                "source_id": source.id,
                "words": words,
                "hash": new_hash,
                "extractor": scrape_res.extractor
            }
        )

        return {
            "source_id": source.id,
            "status": "updated",
            "technology": source.technology,
            "vendor": source.vendor,
            "doc_type": source.doc_type,
            "normalized_content": normalized,
            "words": words,
            "hash": new_hash
        }
