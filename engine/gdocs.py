"""
Google Docs and Drive API integration for SyncLM Studio.
Handles Service Account authentication, document content inspection,
safe range clearing, chunked batch updates, and dry-run simulation.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Optional, Dict, Any, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger("synclm.gdocs")

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive"
]

MAX_CHUNK_CHARS = 45000  # Safe chunk size for Google Docs insertText batch requests


class GoogleDocsClient:
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials = self._load_credentials(credentials_path)
        self._service = None
        self._drive_service = None
        self.service_account_email = None
        if self.credentials:
            self.service_account_email = getattr(self.credentials, "service_account_email", None)

    def _load_credentials(self, credentials_path: Optional[str] = None):
        """Loads credentials from path, env var GCP_SERVICE_ACCOUNT_JSON, GCP_SA_KEY_B64, or ADC."""
        # 1. Base64 environment variable
        b64_key = os.getenv("GCP_SA_KEY_B64")
        if b64_key:
            try:
                decoded = base64.b64decode(b64_key).decode("utf-8")
                info = json.loads(decoded)
                return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            except Exception as e:
                logger.warning(f"Failed to parse GCP_SA_KEY_B64: {e}")

        # 2. Raw JSON string environment variable
        raw_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
        if raw_json:
            try:
                info = json.loads(raw_json)
                return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            except Exception as e:
                logger.warning(f"Failed to parse GCP_SERVICE_ACCOUNT_JSON: {e}")

        # 3. Path from argument or GOOGLE_APPLICATION_CREDENTIALS
        path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if path and os.path.exists(path):
            try:
                return service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load credentials from file {path}: {e}")

        return None

    @property
    def is_configured(self) -> bool:
        return self.credentials is not None

    def get_service(self):
        if not self.credentials:
            raise ValueError("Google Service Account credentials are not configured.")
        if not self._service:
            self._service = build("docs", "v1", credentials=self.credentials, cache_discovery=False)
        return self._service

    def test_document_access(self, doc_id: str) -> Dict[str, Any]:
        """Test read and write permissions for a target Google Doc."""
        if not self.is_configured:
            return {
                "accessible": False,
                "title": None,
                "error": "Google Cloud Service Account credentials are not configured. Run in Dry-Run mode or provide credentials.",
                "service_account_email": None
            }
        try:
            service = self.get_service()
            doc = service.documents().get(documentId=doc_id).execute()
            return {
                "accessible": True,
                "title": doc.get("title", "Untitled Document"),
                "end_index": doc.get("body", {}).get("content", [{}])[-1].get("endIndex", 1),
                "service_account_email": self.service_account_email,
                "error": None
            }
        except HttpError as err:
            err_msg = str(err)
            if err.resp.status == 404:
                msg = f"Google Document '{doc_id}' not found. Verify the ID."
            elif err.resp.status == 403:
                msg = (
                    f"Access Denied (403). Make sure to share the document '{doc_id}' "
                    f"with the Service Account email: {self.service_account_email} as an Editor."
                )
            else:
                msg = f"Google Docs API error: {err_msg}"
            return {
                "accessible": False,
                "title": None,
                "error": msg,
                "service_account_email": self.service_account_email
            }
        except Exception as e:
            return {
                "accessible": False,
                "title": None,
                "error": str(e),
                "service_account_email": self.service_account_email
            }

    def sync_markdown_to_doc(
        self,
        doc_id: str,
        content: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronizes markdown content into designated Google Doc.
        - Reads document length (`endIndex`).
        - Clears existing stale content (range 1 to endIndex - 1).
        - Inserts structured markdown content in safe chunks.
        """
        start_time = time.time()
        char_count = len(content)

        if dry_run or not self.is_configured:
            chunks = self._chunk_content(content, MAX_CHUNK_CHARS)
            return {
                "success": True,
                "dry_run": True,
                "doc_id": doc_id,
                "chars_synced": char_count,
                "chunks_count": len(chunks),
                "duration_seconds": round(time.time() - start_time, 2),
                "message": f"[DRY-RUN] Simulated synchronization of {char_count:,} characters in {len(chunks)} chunks into Google Doc '{doc_id}'."
            }

        try:
            service = self.get_service()
            
            # Step 1: Read current document state
            doc = service.documents().get(documentId=doc_id).execute()
            content_elements = doc.get("body", {}).get("content", [])
            end_index = content_elements[-1].get("endIndex", 1) if content_elements else 1

            requests: List[Dict[str, Any]] = []

            # Step 2: Clear stale content if document already has text (endIndex > 2)
            if end_index > 2:
                requests.append({
                    "deleteContentRange": {
                        "range": {
                            "startIndex": 1,
                            "endIndex": end_index - 1
                        }
                    }
                })

            # Execute the clear operation first if needed
            if requests:
                service.documents().batchUpdate(
                    documentId=doc_id,
                    body={"requests": requests}
                ).execute()

            # Step 3: Chunk content and insert
            chunks = self._chunk_content(content, MAX_CHUNK_CHARS)
            # When inserting at index 1 in reverse order, chunk 0 ends up at the top
            for i, chunk in enumerate(reversed(chunks)):
                insert_req = [{
                    "insertText": {
                        "location": {"index": 1},
                        "text": chunk
                    }
                }]
                service.documents().batchUpdate(
                    documentId=doc_id,
                    body={"requests": insert_req}
                ).execute()

            duration = round(time.time() - start_time, 2)
            return {
                "success": True,
                "dry_run": False,
                "doc_id": doc_id,
                "chars_synced": char_count,
                "chunks_count": len(chunks),
                "duration_seconds": duration,
                "message": f"Successfully synced {char_count:,} characters into Google Doc '{doc_id}'."
            }

        except HttpError as err:
            if err.resp.status == 403:
                err_msg = (
                    f"403 Forbidden: Share document '{doc_id}' with Service Account "
                    f"'{self.service_account_email}' as Editor."
                )
            else:
                err_msg = f"Google Docs API error ({err.resp.status}): {err}"
            return {
                "success": False,
                "dry_run": False,
                "doc_id": doc_id,
                "error": err_msg,
                "duration_seconds": round(time.time() - start_time, 2)
            }
        except Exception as exc:
            return {
                "success": False,
                "dry_run": False,
                "doc_id": doc_id,
                "error": f"Unexpected error during sync: {str(exc)}",
                "duration_seconds": round(time.time() - start_time, 2)
            }

    @staticmethod
    def _chunk_content(text: str, max_size: int) -> List[str]:
        """Splits long text cleanly along newline boundaries if possible."""
        if len(text) <= max_size:
            return [text]

        chunks = []
        lines = text.splitlines(keepends=True)
        current_chunk = []
        current_length = 0

        for line in lines:
            if current_length + len(line) > max_size and current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = [line]
                current_length = len(line)
            else:
                current_chunk.append(line)
                current_length += len(line)

        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks
