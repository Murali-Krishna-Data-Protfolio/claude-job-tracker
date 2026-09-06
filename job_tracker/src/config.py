"""
config.py — loads shared settings + the active user profile.

Multi-user model: every candidate-specific fact (name, target roles, skills,
salary floor, notification email...) lives in profiles/<id>.json, never in
code. Pick which profile loads via the ACTIVE_PROFILE env var (.env).

New user setup:
  1. Copy profiles/example.json -> profiles/<your_id>.json and fill it in.
  2. Set ACTIVE_PROFILE=<your_id> in .env.
  3. Add your own API keys / GMAIL_USER to .env (see .env.example).
No source file needs to change.
"""

import json
import os
import sys
from pathlib import Path

# ── Path roots ──────────────────────────────────────────────────────────────────
# This file lives in <project_root>/src/, so the project root is one level up.
SRC_DIR      = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
PROFILES_DIR = PROJECT_ROOT / "profiles"

# Load .env here too, not just in job_tracker.py/write_jobs.py — otherwise a
# script that imports config directly (sync_cloud.py --setup, sync_gdrive.py
# --setup) never sees ACTIVE_PROFILE from .env and silently falls back to the
# "murali" default below, since profiles/murali.json exists in the repo and
# _load_profile() has no way to know that wasn't the intended profile.
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass

# ── Active profile ────────────────────────────────────────────────────────────
ACTIVE_PROFILE_ID = os.environ.get("ACTIVE_PROFILE", "murali")


def _load_profile(profile_id: str) -> dict:
    path = PROFILES_DIR / f"{profile_id}.json"
    if not path.exists():
        print(f"\n[ERROR] Profile not found: {path}")
        print(f"  Copy profiles/example.json -> profiles/{profile_id}.json and fill it in,")
        print(f"  or set ACTIVE_PROFILE in .env to an existing profile id.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


PROFILE = _load_profile(ACTIVE_PROFILE_ID)

# ── Derived from profile ──────────────────────────────────────────────────────
SEARCH_QUERIES = PROFILE["target_roles"]
TARGET_ROLES   = PROFILE["target_roles"]          # used for category grouping everywhere
LOCATION       = PROFILE.get("location", "France")
COUNTRY_CODE   = PROFILE.get("country_code", "FR")
CANDIDATE_NAME = PROFILE.get("candidate_name", "Candidate")
EMAIL_TO       = PROFILE.get("email_to") or os.environ.get("GMAIL_USER", "")

# ── English filter ─────────────────────────────────────────────────────────────
ENGLISH_CONFIDENCE_THRESHOLD = float(PROFILE.get("english_confidence_threshold", 0.75))

# ── Output (per-profile, so multiple profiles never overwrite each other) ─────
OUTPUT_DIR  = PROJECT_ROOT / "outputs" / ACTIVE_PROFILE_ID
OUTPUT_PATH = str(OUTPUT_DIR / "job_applications.xlsx")

# ── Claude model (haiku = cheapest, fast enough for classification) ────────────
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# ── Status choices for Excel dropdown ─────────────────────────────────────────
STATUS_CHOICES = ["Saved", "Applied", "Interview", "Offer", "Rejected"]

# ── Platform API credentials (read from .env — secrets, never in profiles/) ───
# Adzuna – free at https://developer.adzuna.com/signup
ADZUNA_APP_ID  = os.environ.get("ADZUNA_APP_ID",  "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")

# RapidAPI / JSearch – free tier at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
RAPIDAPI_KEY   = os.environ.get("RAPIDAPI_KEY", "")

# ── Platform enable flags (auto-disabled if key missing) ──────────────────────
PLATFORMS = {
    "indeed":        False,                    # works only in cloud CCR (MCP tool) – off locally
    "wttj":          False,                    # API returns 0 results – disabled
    "talentio":      False,                    # domain DNS error – disabled
    "jobsinnetwork": False,                    # JS-rendered SPA, requires headless browser – disabled
    "francetravail": False,                    # French-only jobs (0 English hits) – Adzuna already covers these boards
    "adzuna":        bool(ADZUNA_APP_ID),      # needs free key
    "jsearch":       bool(RAPIDAPI_KEY),       # covers LinkedIn + Glassdoor
}
