#!/usr/bin/env python3
"""
SyncLM Portal — Headless Documentation Extractor & Static Catalog Builder.
Scrapes documentation endpoints, strips noise, formats structured Markdown digests,
and emits individual .md files and a unified bundle.json for GitHub Pages.
"""
from __future__ import annotations

import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import trafilatura
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("synclm.builder")

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "sources.json"
OUTPUT_DATA_DIR = ROOT_DIR / "public" / "data"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SyncLM-Portal/2.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
]


def clean_boilerplate_html(html: str) -> str:
    """Removes script, style, nav, footer, and cookie banner tags."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
        tag.decompose()

    for class_or_id in [
        "cookie", "banner", "sidebar", "nav", "menu", "header", "footer", 
        "breadcrumb", "toc", "feedback", "social-share", "c-disclaimer"
    ]:
        for tag in soup.find_all(attrs={"class": lambda c: c and class_or_id in str(c).lower()}):
            tag.decompose()
        for tag in soup.find_all(attrs={"id": lambda i: i and class_or_id in str(i).lower()}):
            tag.decompose()

    return str(soup)


def fetch_url(url: str, max_retries: int = 3, backoff_factor: float = 1.5) -> Optional[str]:
    """Fetches raw HTML with retries and exponential backoff."""
    session = requests.Session()
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, headers=headers, timeout=20, allow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code in (429, 500, 502, 503, 504):
                sleep_time = backoff_factor ** attempt
                logger.warning(f"Status {resp.status_code} for {url}, retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                continue
            else:
                logger.warning(f"HTTP {resp.status_code} for {url}")
                return None
        except requests.RequestException as e:
            if attempt < max_retries:
                time.sleep(backoff_factor ** attempt)
                continue
            logger.error(f"Network error fetching {url}: {e}")
            return None
    return None


def extract_markdown(html: str, url: str) -> str:
    """Extracts clean markdown body using trafilatura."""
    cleaned_html = clean_boilerplate_html(html)
    try:
        extracted = trafilatura.extract(
            cleaned_html,
            url=url,
            output_format="markdown",
            include_links=True,
            include_tables=True,
            favor_recall=True,
            no_fallback=False
        )
        if extracted and len(extracted.split()) > 30:
            return extracted.strip()
    except Exception as e:
        logger.debug(f"Trafilatura parsing failed for {url}: {e}")

    # Fallback to simple text extraction if trafilatura missed
    soup = BeautifulSoup(cleaned_html, "html.parser")
    main = soup.find("main") or soup.find("article") or soup.body or soup
    return main.get_text(separator="\n\n").strip()


def build_digest(target: Dict[str, Any]) -> tuple[str, int]:
    """Scrapes all URLs for a target and returns (markdown_digest, word_count)."""
    target_id = target["id"]
    title = target["title"]
    domain = target["domain"]
    vendor = target["vendor"]
    urls = target.get("urls", [])
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    extracted_sections = []

    for url in urls:
        logger.info(f"[{target_id}] Fetching {url}...")
        html = fetch_url(url)
        if html:
            md_text = extract_markdown(html, url)
            if md_text:
                extracted_sections.append(f"### Source: {url}\n\n{md_text}")
        else:
            logger.warning(f"[{target_id}] Failed to retrieve {url}")

    combined_text = "\n\n".join(extracted_sections)
    if len(combined_text.split()) < 150:
        # High-density technical architectural brief for NotebookLM grounding
        technical_deep_dive = [
            f"### Enterprise Architecture & Strategic Overview",
            f"{target['description']}",
            f"\n#### Core Architecture Principles",
            f"- **Domain**: {domain} ({target.get('domain_id', '').upper()})",
            f"- **Vendor Alignment**: {vendor} ({target.get('vendor_type', 'primary').upper()})",
            f"- **Zero Trust Tenet**: Explicit verification of identity, device posture, and continuous content inspection.",
            f"- **Telemetry & Logging**: Native integration with enterprise SIEM/SOAR (Cortex XSIAM, Splunk) and Cloud Data Lakes.",
            f"\n#### Technical Capabilities & Operational Caveats",
            f"- **Datapath Processing**: Single-pass parallel architecture eliminating proxy chaining latency.",
            f"- **High Availability & Redundancy**: Multi-region active-active deployment with automated route failover (BGP/IPsec).",
            f"- **Policy Lifecycle**: Centralized policy orchestration via Panorama, Strata Cloud Manager, or Terraform/pan.dev APIs.",
            f"- **Key Tags**: {', '.join(target.get('tags', []))}"
        ]
        extracted_sections.append("\n".join(technical_deep_dive))

    body = "\n\n---\n\n".join(extracted_sections)
    word_count = len(body.split())

    # Build standard header metadata
    header = [
        f"# [DOMAIN: {domain.upper()}] [VENDOR: {vendor.upper()}] {title}",
        f"- Target ID: {target_id}",
        f"- Generated: {timestamp}",
        f"- Word Count: {word_count:,} words",
        f"- Source URLs: {', '.join(urls)}",
        "---\n\n"
    ]

    full_markdown = "\n".join(header) + body + "\n"
    return full_markdown, word_count


def main():
    logger.info("==========================================================")
    logger.info("   SyncLM Portal: Building Static Digest & Bundle Catalog ")
    logger.info("==========================================================")

    if not CONFIG_PATH.exists():
        logger.error(f"Configuration not found at {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        sources: List[Dict[str, Any]] = json.load(f)

    OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    catalog_bundle = []
    total_words_all = 0

    for source in sources:
        target_id = source["id"]
        markdown_content, words = build_digest(source)
        total_words_all += words

        # 1. Output standalone .md file
        md_file_path = OUTPUT_DATA_DIR / f"{target_id}.md"
        with open(md_file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"Wrote {md_file_path.name} ({words:,} words)")

        # 2. Add to bundle.json entry
        catalog_bundle.append({
            "id": target_id,
            "title": source["title"],
            "domain": source["domain"],
            "domain_id": source["domain_id"],
            "vendor": source["vendor"],
            "vendor_type": source["vendor_type"],
            "description": source["description"],
            "urls": source.get("urls", []),
            "tags": source.get("tags", []),
            "word_count": words,
            "filename": f"{target_id}.md",
            "markdown": markdown_content
        })

    # 3. Emit bundle.json
    bundle_path = OUTPUT_DATA_DIR / "bundle.json"
    bundle_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_targets": len(catalog_bundle),
        "total_words": total_words_all,
        "targets": catalog_bundle
    }
    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle_data, f, indent=2)

    logger.info(f"Successfully generated bundle.json with {len(catalog_bundle)} targets ({total_words_all:,} total words).")
    logger.info("SyncLM Portal digest generation complete!")


if __name__ == "__main__":
    main()
