"""
write_jobs.py — called by the daily Claude Code agent after fetching jobs via MCP.

Usage:
    python write_jobs.py raw_jobs.json

The agent saves raw Indeed results to raw_jobs.json, then calls this script
to filter for English-speaking roles and append them to the Excel tracker.
"""

import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass

from config import OUTPUT_PATH
from excel_writer import (
    _build_dashboard,
    _ensure_jobs_sheet,
    _load_or_create,
    append_jobs,
    load_existing_job_ids,
    save_workbook,
)
from job_fetcher import filter_english_jobs


def main():
    if len(sys.argv) < 2:
        print("Usage: python write_jobs.py <raw_jobs.json>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"[ERROR] File not found: {input_file}")
        sys.exit(1)

    with open(input_file, encoding="utf-8") as f:
        raw_jobs = json.load(f)

    print(f"Loaded {len(raw_jobs)} raw jobs from {input_file}")

    # Load workbook and get existing IDs
    wb, _ = _load_or_create()
    _ensure_jobs_sheet(wb)
    existing_ids = load_existing_job_ids(wb)

    # Deduplicate
    new_jobs = [j for j in raw_jobs if str(j.get("job_id", "")) not in existing_ids]
    print(f"New jobs (not yet tracked): {len(new_jobs)}  |  Duplicates skipped: {len(raw_jobs) - len(new_jobs)}")

    if not new_jobs:
        print("Nothing new to add.")
        _build_dashboard(wb)
        save_workbook(wb)
        return

    # Filter for English-speaking roles
    english_jobs = filter_english_jobs(new_jobs)

    # Write to Excel
    added = append_jobs(wb, english_jobs)
    _build_dashboard(wb)
    save_workbook(wb)

    print(f"\nDone. Added {added} new English-speaking jobs.")
    print(f"Tracker: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
