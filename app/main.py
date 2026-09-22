"""
SyncLM Studio FastAPI Application & Controller.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import List, Set, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIST, DEBUG
from app.schemas import (
    SyncRequest,
    TargetCreateOrUpdate,
    TargetTestRequest,
    BudgetCalculateRequest
)
from engine.sources import (
    TECHNOLOGIES,
    VENDORS,
    DOC_TYPES,
    load_doc_sources,
    load_targets,
    save_targets,
    filter_sources,
    calculate_notebooklm_budget,
    DocTarget
)
from engine.gdocs import GoogleDocsClient
from engine.dedup import HashStore
from engine.pipeline import SyncPipeline, PipelineEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("synclm.api")

app = FastAPI(
    title="SyncLM Studio API",
    description="Interactive Web App & TechDocs Sync Pipeline for NotebookLM",
    version="1.0.0"
)

# CORS setup for Vite frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory broadcast manager for SSE log listeners
class ConnectionManager:
    def __init__(self):
        self.active_queues: Set[asyncio.Queue] = set()
        self.recent_logs: List[dict] = []
        self.max_recent = 200
        self.is_running = False
        self.latest_summary: Optional[dict] = None

    def register(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.active_queues.add(q)
        return q

    def unregister(self, q: asyncio.Queue):
        self.active_queues.discard(q)

    async def broadcast(self, event: PipelineEvent):
        event_dict = event.to_dict()
        self.recent_logs.append(event_dict)
        if len(self.recent_logs) > self.max_recent:
            self.recent_logs.pop(0)

        for q in list(self.active_queues):
            try:
                await q.put(event_dict)
            except Exception:
                self.active_queues.discard(q)


manager = ConnectionManager()
gdocs_client = GoogleDocsClient()
hash_store = HashStore()


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SyncLM Studio",
        "gdocs_configured": gdocs_client.is_configured,
        "service_account_email": gdocs_client.service_account_email
    }


@app.get("/api/metadata")
async def get_metadata():
    return {
        "technologies": TECHNOLOGIES,
        "vendors": VENDORS,
        "doc_types": DOC_TYPES
    }


@app.get("/api/sources")
async def get_sources(
    technology: Optional[str] = None,
    vendor: Optional[str] = None,
    doc_type: Optional[str] = None
):
    sources = load_doc_sources()
    techs = [technology] if technology and technology != "all" else None
    vends = [vendor] if vendor and vendor != "all" else None
    dts = [doc_type] if doc_type and doc_type != "all" else None
    filtered = filter_sources(sources, technologies=techs, vendors=vends, doc_types=dts)
    return [s.model_dump() for s in filtered]


@app.get("/api/targets")
async def get_targets():
    return [t.model_dump() for t in load_targets()]


@app.post("/api/targets")
async def create_or_update_target(item: TargetCreateOrUpdate):
    targets = load_targets()
    target_id = item.id or f"target-{item.technology}-{uuid.uuid4().hex[:6]}"
    
    updated = False
    new_list = []
    for t in targets:
        if t.id == target_id:
            updated_target = DocTarget(
                id=target_id,
                name=item.name,
                technology=item.technology,
                vendor=item.vendor,
                google_doc_id=item.google_doc_id.strip(),
                description=item.description,
                last_synced=t.last_synced,
                status=t.status
            )
            new_list.append(updated_target)
            updated = True
        else:
            new_list.append(t)

    if not updated:
        new_target = DocTarget(
            id=target_id,
            name=item.name,
            technology=item.technology,
            vendor=item.vendor,
            google_doc_id=item.google_doc_id.strip(),
            description=item.description,
            status="unverified"
        )
        new_list.append(new_target)

    save_targets(new_list)
    return {"status": "success", "id": target_id}


@app.delete("/api/targets/{target_id}")
async def delete_target(target_id: str):
    targets = load_targets()
    filtered = [t for t in targets if t.id != target_id]
    if len(filtered) == len(targets):
        raise HTTPException(status_code=404, detail="Target not found")
    save_targets(filtered)
    return {"status": "deleted", "id": target_id}


@app.post("/api/targets/test")
async def test_target(req: TargetTestRequest):
    res = gdocs_client.test_document_access(req.google_doc_id.strip())
    # If accessible, update target status
    if res.get("accessible"):
        targets = load_targets()
        for t in targets:
            if t.google_doc_id == req.google_doc_id.strip():
                t.status = "verified"
        save_targets(targets)
    return res


@app.post("/api/budget")
async def calculate_budget(req: BudgetCalculateRequest):
    all_sources = load_doc_sources()
    if req.selected_source_ids:
        id_set = set(req.selected_source_ids)
        selected = [s for s in all_sources if s.id in id_set]
    else:
        selected = filter_sources(
            all_sources,
            technologies=req.technologies,
            vendors=req.vendors,
            doc_types=req.doc_types
        )
    targets = load_targets()
    return calculate_notebooklm_budget(selected, target_count=max(1, len(targets)))


@app.post("/api/sync")
async def trigger_sync(req: SyncRequest, background_tasks: BackgroundTasks):
    if manager.is_running:
        raise HTTPException(status_code=409, detail="A sync job is already in progress.")

    manager.is_running = True

    async def run_job():
        try:
            queue = asyncio.Queue()
            pipeline = SyncPipeline(event_queue=queue, dry_run=req.dry_run)

            # Broadcast worker
            async def broadcast_loop():
                while manager.is_running:
                    try:
                        event: PipelineEvent = await asyncio.wait_for(queue.get(), timeout=0.5)
                        await manager.broadcast(event)
                        queue.task_done()
                        if event.event_type == "complete":
                            break
                    except asyncio.TimeoutError:
                        continue

            broadcast_task = asyncio.create_task(broadcast_loop())

            summary = await pipeline.run(
                technologies=req.technologies,
                vendors=req.vendors,
                doc_types=req.doc_types,
                selected_source_ids=req.selected_source_ids,
                dry_run=req.dry_run
            )

            await broadcast_task
            manager.latest_summary = summary
        except Exception as exc:
            logger.error(f"Sync execution error: {exc}", exc_info=True)
            err_event = PipelineEvent("error", f"Pipeline error: {str(exc)}", level="ERROR")
            await manager.broadcast(err_event)
        finally:
            manager.is_running = False

    background_tasks.add_task(run_job)
    return {"status": "started", "dry_run": req.dry_run}


@app.get("/api/sync/status")
async def get_sync_status():
    return {
        "is_running": manager.is_running,
        "latest_summary": manager.latest_summary,
        "recent_logs_count": len(manager.recent_logs)
    }


@app.get("/api/sync/stream")
async def sync_stream():
    """Server-Sent Events endpoint streaming real-time pipeline events."""
    queue = manager.register()

    async def event_generator():
        try:
            # Emit backlogged logs first
            for old_event in manager.recent_logs[-30:]:
                yield f"data: {json.dumps(old_event)}\n\n"

            # Stream live events
            while True:
                event_dict = await queue.get()
                yield f"data: {json.dumps(event_dict)}\n\n"
                queue.task_done()
        except asyncio.CancelledError:
            pass
        finally:
            manager.unregister(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/hashes")
async def get_hashes_stats():
    return hash_store.get_stats()


from app.config import PUBLIC_DIR

# Mount public directory for static assets and single-page dashboard
if PUBLIC_DIR.exists():
    if (PUBLIC_DIR / "data").exists():
        app.mount("/data", StaticFiles(directory=PUBLIC_DIR / "data"), name="public_data")

    @app.get("/{full_path:path}")
    async def serve_portal(full_path: str):
        file_path = PUBLIC_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(PUBLIC_DIR / "index.html")
