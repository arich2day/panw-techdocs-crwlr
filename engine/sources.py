"""
Source registry and taxonomy definitions for SyncLM Studio.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Constants for verticals and vendors
TECHNOLOGIES = [
    {"id": "sase", "name": "SASE / SSE", "description": "Prisma Access, Cloud SWG, ZTNA, CASB"},
    {"id": "browser", "name": "Enterprise Browser", "description": "Prisma Access Browser, Island, Chromium Isolation"},
    {"id": "ngfw", "name": "Next-Gen Firewall / PAN-OS", "description": "Hardware, VM-Series, SP3 Architecture"},
    {"id": "secops", "name": "Cortex / SecOps", "description": "XDR, XSOAR, XSIAM Autonomous SOC"},
    {"id": "cloud", "name": "Cloud Security", "description": "Prisma Cloud, CNAPP, CSPM, CWPP"}
]

VENDORS = [
    {"id": "panw", "name": "Palo Alto Networks", "is_primary": True, "badge": "PANW Core"},
    {"id": "zscaler", "name": "Zscaler", "is_primary": False, "badge": "Competitor"},
    {"id": "netskope", "name": "Netskope", "is_primary": False, "badge": "Competitor"},
    {"id": "island", "name": "Island", "is_primary": False, "badge": "Competitor"},
    {"id": "cloudflare", "name": "Cloudflare One", "is_primary": False, "badge": "Competitor"},
    {"id": "fortinet", "name": "Fortinet", "is_primary": False, "badge": "Competitor"}
]

DOC_TYPES = [
    {"id": "architecture", "name": "Architecture Guides", "description": "Reference designs, topology, packet flow"},
    {"id": "release_notes", "name": "Release Notes & Known Issues", "description": "Version caveats, breaking changes, advisories"},
    {"id": "api_specs", "name": "pan.dev & OpenAPI Specs", "description": "Developer schemas, endpoints, SDK guides"},
    {"id": "battlecards", "name": "Competitive Battlecards", "description": "Architectural matrices, pros/cons, differentiators"}
]


class DocSource(BaseModel):
    id: str
    title: str
    technology: str  # sase, browser, ngfw, secops, cloud
    vendor: str      # panw, zscaler, netskope, island, cloudflare, fortinet
    doc_type: str    # architecture, release_notes, api_specs, battlecards
    url: str
    word_estimate: int = 5000
    priority: int = 1
    description: Optional[str] = ""


class DocTarget(BaseModel):
    id: str
    name: str
    technology: str
    vendor: str = "all"
    google_doc_id: str
    description: Optional[str] = ""
    last_synced: Optional[str] = None
    status: str = "unverified"


def get_data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def load_doc_sources(file_path: Optional[Path] = None) -> List[DocSource]:
    path = file_path or (get_data_dir() / "doc_sources.json")
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [DocSource(**item) for item in data]


def save_doc_sources(sources: List[DocSource], file_path: Optional[Path] = None) -> None:
    path = file_path or (get_data_dir() / "doc_sources.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([s.model_dump() for s in sources], f, indent=2)


def load_targets(file_path: Optional[Path] = None) -> List[DocTarget]:
    path = file_path or (get_data_dir() / "targets.json")
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [DocTarget(**item) for item in data.get("targets", [])]


def save_targets(targets: List[DocTarget], file_path: Optional[Path] = None) -> None:
    path = file_path or (get_data_dir() / "targets.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"targets": [t.model_dump() for t in targets]}, f, indent=2)


def filter_sources(
    sources: List[DocSource],
    technologies: Optional[List[str]] = None,
    vendors: Optional[List[str]] = None,
    doc_types: Optional[List[str]] = None
) -> List[DocSource]:
    filtered = sources
    if technologies:
        tech_set = set(technologies)
        filtered = [s for s in filtered if s.technology in tech_set]
    if vendors:
        vendor_set = set(vendors)
        filtered = [s for s in filtered if s.vendor in vendor_set]
    if doc_types:
        dt_set = set(doc_types)
        filtered = [s for s in filtered if s.doc_type in dt_set]
    return filtered


def calculate_notebooklm_budget(selected_sources: List[DocSource], target_count: int = 5) -> Dict[str, Any]:
    """
    Computes NotebookLM slot and word budgets.
    NotebookLM allows max 50 sources per notebook, max 500,000 words per source.
    """
    total_words = sum(s.word_estimate for s in selected_sources)
    estimated_tokens = int(total_words * 1.33)
    
    # In SyncLM Studio, each Target Google Doc represents 1 NotebookLM source slot
    # e.g., if docs are grouped into target docs per technology, we consume 1 slot per target doc.
    # If users ingest individual articles directly, it consumes 1 slot per source article.
    slot_usage_consolidated = min(target_count, len(selected_sources))
    slot_usage_unconsolidated = len(selected_sources)
    
    max_slots = 50
    max_words_per_doc = 500000
    
    avg_words_per_target = total_words // max(1, slot_usage_consolidated)
    
    status = "optimal"
    warnings = []
    
    if slot_usage_consolidated > max_slots:
        status = "danger"
        warnings.append(f"Exceeds NotebookLM 50-source slot limit ({slot_usage_consolidated}/{max_slots})")
    elif slot_usage_consolidated > 40:
        status = "warning"
        warnings.append(f"Approaching NotebookLM slot capacity ({slot_usage_consolidated}/{max_slots})")
        
    if avg_words_per_target > max_words_per_doc:
        status = "danger"
        warnings.append(f"Average target doc words exceed NotebookLM 500,000 word limit ({avg_words_per_target:,} words)")
        
    return {
        "source_count": len(selected_sources),
        "total_words": total_words,
        "estimated_tokens": estimated_tokens,
        "slot_usage_consolidated": slot_usage_consolidated,
        "slot_usage_unconsolidated": slot_usage_unconsolidated,
        "max_slots": max_slots,
        "avg_words_per_target": avg_words_per_target,
        "max_words_per_target": max_words_per_doc,
        "status": status,
        "warnings": warnings
    }
