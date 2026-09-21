import pytest
from engine.sources import (
    DocSource,
    load_doc_sources,
    filter_sources,
    calculate_notebooklm_budget,
    TECHNOLOGIES,
    VENDORS
)


def test_load_doc_sources():
    sources = load_doc_sources()
    assert len(sources) > 0
    panw_sources = [s for s in sources if s.vendor == "panw"]
    assert len(panw_sources) >= 5


def test_filter_sources():
    sources = load_doc_sources()
    
    # Filter by tech
    sase_only = filter_sources(sources, technologies=["sase"])
    assert all(s.technology == "sase" for s in sase_only)
    assert len(sase_only) > 0

    # Filter by vendor
    panw_only = filter_sources(sources, vendors=["panw"])
    assert all(s.vendor == "panw" for s in panw_only)

    # Combined filter
    sase_panw = filter_sources(sources, technologies=["sase"], vendors=["panw"])
    assert all(s.technology == "sase" and s.vendor == "panw" for s in sase_panw)


def test_calculate_notebooklm_budget():
    sources = load_doc_sources()
    budget = calculate_notebooklm_budget(sources, target_count=5)
    
    assert budget["source_count"] == len(sources)
    assert budget["total_words"] > 0
    assert budget["slot_usage_consolidated"] <= 5
    assert budget["status"] in ("optimal", "warning", "danger")
