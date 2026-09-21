"""
Document normalization and structured metadata injection for NotebookLM ingestion.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional


def build_metadata_header(
    title: str,
    vendor: str,
    technology: str,
    doc_type: str,
    url: str,
    timestamp: Optional[str] = None
) -> str:
    """
    Builds the standardized header metadata required for NotebookLM grounding:
    # [VENDOR: PANW] [TECH: SASE] Document Title
    - Source: <URL>
    - Synced: <TIMESTAMP>
    - Doc Type: <DOC_TYPE>
    ---
    """
    ts = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    v_upper = vendor.upper()
    t_upper = technology.upper()
    dt_upper = doc_type.upper().replace("_", " ")

    header_lines = [
        f"# [VENDOR: {v_upper}] [TECH: {t_upper}] {title.strip()}",
        f"- Source: {url.strip()}",
        f"- Synced: {ts}",
        f"- Doc Type: {dt_upper}",
        "---\n"
    ]
    return "\n".join(header_lines)


def clean_markdown_body(text: str) -> str:
    """
    Cleans raw markdown text:
    - Strips unwanted navigation leftovers and cookie warnings
    - Normalizes excessive blank lines
    - Fixes markdown table separators and irregular line breaks
    - Ensures clean heading spacing
    """
    if not text:
        return ""

    # Remove residual HTML script/style remnants
    cleaned = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove common boilerplate patterns
    boilerplate_patterns = [
        r"(?i)was this page helpful\?.*",
        r"(?i)accept all cookies.*",
        r"(?i)cookie preferences.*",
        r"(?i)all rights reserved.*",
        r"(?i)terms of use.*privacy policy.*"
    ]
    for bp in boilerplate_patterns:
        cleaned = re.sub(bp, "", cleaned)

    # Normalize heading spacing: ensure empty line before headings
    cleaned = re.sub(r"([^\n])\n(#{1,6}\s+)", r"\1\n\n\2", cleaned)

    # Normalize multiple blank lines down to max 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Trim lines
    lines = [line.rstrip() for line in cleaned.splitlines()]
    return "\n".join(lines).strip()


def normalize_document(
    title: str,
    raw_content: str,
    vendor: str,
    technology: str,
    doc_type: str,
    url: str,
    timestamp: Optional[str] = None
) -> str:
    """
    Combines standardized header metadata with sanitized markdown content.
    """
    header = build_metadata_header(
        title=title,
        vendor=vendor,
        technology=technology,
        doc_type=doc_type,
        url=url,
        timestamp=timestamp
    )
    body = clean_markdown_body(raw_content)
    return f"{header}\n{body}\n"
