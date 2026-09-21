"""
Pydantic schemas for FastAPI endpoints in SyncLM Studio.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SyncRequest(BaseModel):
    technologies: Optional[List[str]] = None
    vendors: Optional[List[str]] = None
    doc_types: Optional[List[str]] = None
    selected_source_ids: Optional[List[str]] = None
    dry_run: bool = True


class TargetCreateOrUpdate(BaseModel):
    id: Optional[str] = None
    name: str
    technology: str
    vendor: str = "all"
    google_doc_id: str
    description: Optional[str] = ""


class TargetTestRequest(BaseModel):
    google_doc_id: str


class BudgetCalculateRequest(BaseModel):
    technologies: Optional[List[str]] = None
    vendors: Optional[List[str]] = None
    doc_types: Optional[List[str]] = None
    selected_source_ids: Optional[List[str]] = None
