#!/usr/bin/env python3
"""
Credentials verification utility for SyncLM Studio Google Docs & Drive API.
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from engine.gdocs import GoogleDocsClient
from dotenv import load_dotenv

load_dotenv()

client = GoogleDocsClient()

print("===================================================================")
print("   SyncLM Studio — Google Cloud Credentials Verification          ")
print("===================================================================")
if not client.is_configured:
    print("STATUS: NOT CONFIGURED")
    print("No Service Account credentials detected.")
    print("To enable live Google Docs synchronization:")
    print("1. Set GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json")
    print("2. Or set GCP_SERVICE_ACCOUNT_JSON='{...}'")
    print("3. Or set GCP_SA_KEY_B64=<base64>")
    print("Note: The app will continue to operate seamlessly in DRY-RUN mode.")
else:
    print("STATUS: CONFIGURED")
    print(f"Service Account Email : {client.service_account_email}")
    print("\nIMPORTANT: To grant sync access, share your target Google Docs with this email as 'Editor'.")
print("===================================================================")
