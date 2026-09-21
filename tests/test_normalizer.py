from engine.normalizer import build_metadata_header, clean_markdown_body, normalize_document


def test_build_metadata_header():
    header = build_metadata_header(
        title="Prisma Access Architecture",
        vendor="panw",
        technology="sase",
        doc_type="architecture",
        url="https://docs.paloaltonetworks.com/prisma",
        timestamp="2026-09-21 12:00:00 UTC"
    )
    assert "# [VENDOR: PANW] [TECH: SASE] Prisma Access Architecture" in header
    assert "- Source: https://docs.paloaltonetworks.com/prisma" in header
    assert "- Synced: 2026-09-21 12:00:00 UTC" in header
    assert "- Doc Type: ARCHITECTURE" in header
    assert "---" in header


def test_clean_markdown_body():
    raw = """
    Accept all cookies
    
    ## Overview
    
    This is technical content.
    
    <script>alert('bad');</script>
    
    Was this page helpful? Yes / No
    """
    cleaned = clean_markdown_body(raw)
    assert "<script>" not in cleaned
    assert "Accept all cookies" not in cleaned
    assert "Was this page helpful" not in cleaned
    assert "## Overview" in cleaned
    assert "This is technical content." in cleaned


def test_normalize_document():
    doc = normalize_document(
        title="Test Title",
        raw_content="Body paragraph here.",
        vendor="panw",
        technology="ngfw",
        doc_type="release_notes",
        url="https://pan.dev"
    )
    assert "# [VENDOR: PANW] [TECH: NGFW] Test Title" in doc
    assert "Body paragraph here." in doc
