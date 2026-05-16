"""
sync_gdrive.py — Upload job_applications.xlsx to Google Drive.

Uploads the Excel DB to a "Job Tracker" folder in gkmurali37@gmail.com's Drive.
File stays in-place (same file ID) so the share link never changes.

First run:  python sync_gdrive.py --setup
Daily run:  called automatically by job_tracker.py
"""

import json
import os
import sys
from pathlib import Path

ENV_PATH    = Path(__file__).parent / ".env"
TOKEN_PATH  = Path(__file__).parent / "gdrive_token.json"
CREDS_PATH  = Path(__file__).parent / "credentials.json"

EXCEL_PATH  = Path(__file__).parent / "outputs" / "job_applications.xlsx"
FOLDER_NAME = "Job Tracker"
FILE_NAME   = "job_applications.xlsx"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# ── .env helpers ──────────────────────────────────────────────────────────────

def _read_env() -> dict:
    if not ENV_PATH.exists():
        return {}
    out = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def _write_env_key(key: str, value: str):
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── OAuth helpers ─────────────────────────────────────────────────────────────

def _get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDS_PATH}\n"
                    "  Follow the setup instructions in README.md to download it."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _get_drive_service():
    from googleapiclient.discovery import build
    creds = _get_credentials()
    return build("drive", "v3", credentials=creds, cache_discovery=False)


# ── Drive operations ──────────────────────────────────────────────────────────

def _find_or_create_folder(service) -> str:
    """Returns the Drive folder ID for 'Job Tracker', creating it if needed."""
    env = _read_env()
    folder_id = env.get("GDRIVE_FOLDER_ID", "")
    if folder_id:
        return folder_id

    # Search for existing folder
    q = f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=q, fields="files(id,name)").execute()
    files = results.get("files", [])
    if files:
        folder_id = files[0]["id"]
    else:
        meta = {
            "name": FOLDER_NAME,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = service.files().create(body=meta, fields="id").execute()
        folder_id = folder["id"]

    _write_env_key("GDRIVE_FOLDER_ID", folder_id)
    return folder_id


def _upload_or_update(service, folder_id: str) -> tuple[str, str]:
    """Upload or update the Excel file. Returns (file_id, view_url)."""
    from googleapiclient.http import MediaFileUpload

    env = _read_env()
    file_id = env.get("GDRIVE_FILE_ID", "")

    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    media = MediaFileUpload(str(EXCEL_PATH), mimetype=mime, resumable=False)

    if file_id:
        # Update existing file (keeps same link)
        service.files().update(
            fileId=file_id,
            media_body=media,
        ).execute()
    else:
        meta = {"name": FILE_NAME, "parents": [folder_id]}
        f = service.files().create(
            body=meta, media_body=media, fields="id"
        ).execute()
        file_id = f["id"]
        _write_env_key("GDRIVE_FILE_ID", file_id)

        # Make it readable by anyone with the link
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()

    view_url = f"https://drive.google.com/file/d/{file_id}/view"
    return file_id, view_url


# ── Public API ─────────────────────────────────────────────────────────────────

def setup_gdrive() -> str:
    """
    First-time setup: authenticate, create folder, upload file.
    Run once with: python sync_gdrive.py --setup
    Returns the permanent Drive link.
    """
    print("\n=== Google Drive Setup ===")

    if not CREDS_PATH.exists():
        print("""
  credentials.json not found. Follow these steps:

  1. Go to: https://console.cloud.google.com/
  2. Create a project (or select existing)
  3. Enable 'Google Drive API':
       APIs & Services -> Library -> search "Google Drive API" -> Enable
  4. Create credentials:
       APIs & Services -> Credentials -> Create Credentials -> OAuth client ID
       Application type: Desktop app  |  Name: JobTracker
  5. Download JSON -> rename to credentials.json
  6. Place it at: C:\\Claude\\job_tracker\\credentials.json
  7. Re-run: python sync_gdrive.py --setup
""")
        sys.exit(1)

    print("\n[1/3] Authenticating with Google (browser will open)...")
    service = _get_drive_service()
    print("  Authenticated OK")

    print(f"\n[2/3] Creating '{FOLDER_NAME}' folder in Drive...")
    folder_id = _find_or_create_folder(service)
    print(f"  Folder ID: {folder_id}")

    print("\n[3/3] Uploading job_applications.xlsx...")
    file_id, view_url = _upload_or_update(service, folder_id)
    _write_env_key("GDRIVE_VIEW_URL", view_url)

    print(f"\n=== Setup Complete ===")
    print(f"  Drive link : {view_url}")
    print(f"\n  On your phone:")
    print(f"    1. Install 'Google Drive' app (sign in as gkmurali37@gmail.com)")
    print(f"    2. Or open: {view_url}")
    print()
    return view_url


def sync_gdrive(verbose: bool = True) -> str | None:
    """
    Upload the latest Excel file to Drive. Called by job_tracker.py automatically.
    Returns the view URL or None if not configured.
    """
    env = _read_env()
    if not TOKEN_PATH.exists() and not env.get("GDRIVE_FILE_ID"):
        if verbose:
            print("  [gdrive] Not set up yet. Run: python sync_gdrive.py --setup")
        return None

    if not EXCEL_PATH.exists():
        if verbose:
            print("  [gdrive] Excel file not found — skipped")
        return None

    try:
        service = _get_drive_service()
        folder_id = _find_or_create_folder(service)
        file_id, view_url = _upload_or_update(service, folder_id)
        if verbose:
            print(f"  Google Drive updated: {view_url}")
        return view_url
    except Exception as e:
        if verbose:
            print(f"  [warn] Google Drive sync failed: {e}")
        env = _read_env()
        return env.get("GDRIVE_VIEW_URL")


if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup_gdrive()
    else:
        url = sync_gdrive()
        if url:
            print(f"Drive updated: {url}")
