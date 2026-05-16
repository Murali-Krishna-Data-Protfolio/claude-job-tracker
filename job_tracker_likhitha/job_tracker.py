"""
Job Apply Tracker â€” Main Orchestrator
Run daily (manually or via Task Scheduler) to fetch new English-speaking
Data/Analytics jobs in France from Indeed and update the Excel tracker.

Usage:
    python job_tracker.py
"""

import os
import smtplib
import sys
import time
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Load .env if present (ANTHROPIC_API_KEY)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass

from config import OUTPUT_PATH, PLATFORMS, SEARCH_QUERIES
from excel_writer import (
    _build_dashboard,
    _ensure_jobs_sheet,
    _load_or_create,
    append_jobs,
    load_existing_job_ids,
    save_workbook,
)
from job_fetcher import fetch_all_jobs, filter_english_jobs
from sync_bookmarks import sync_bookmarks
from sync_cloud import sync_cloud
from sync_gdrive import sync_gdrive

GMAIL_USER      = "gkmurali37@gmail.com"
GMAIL_PASS      = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_USER)


def banner(text: str):
    width = 60
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def check_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key or not key.startswith("sk-"):
        print("\n[ERROR] ANTHROPIC_API_KEY not set or invalid.")
        print("  Set it in C:\\Claude\\job_tracker_likhitha\\.env  as:")
        print("  ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)


def _count_by_category(jobs: list[dict]) -> dict[str, int]:
    cats: dict[str, int] = {}
    for j in jobs:
        title = j.get("Title") or j.get("title") or ""
        cat = "Other"
        for kw in ["Data Analyst", "Data Engineer", "Business Analyst", "BI Developer", "Analytics Engineer"]:
            if kw.lower() in title.lower():
                cat = kw
                break
        cats[cat] = cats.get(cat, 0) + 1
    return cats


def send_db_update_email(added: int, total_before: int, total_after: int, new_jobs: list[dict], elapsed: float):
    today_str = date.today().strftime("%B %d, %Y")
    cats = _count_by_category(new_jobs)

    # Build breakdown rows
    breakdown_rows = ""
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        breakdown_rows += f"""
        <tr>
          <td style='padding:8px 12px;color:#333;font-size:14px;'>{cat}</td>
          <td style='padding:8px 12px;text-align:center;'>
            <span style='background:#e3f2fd;color:#1565c0;border-radius:12px;padding:2px 10px;font-size:13px;font-weight:bold;'>+{count}</span>
          </td>
        </tr>"""

    active_platforms = [k for k, v in PLATFORMS.items() if v]
    platforms_str = " &bull; ".join({
        "indeed": "Indeed", "wttj": "WelcomeToJungle",
        "talentio": "Talent.io", "adzuna": "Adzuna",
        "jsearch": "LinkedIn/Glassdoor",
    }.get(p, p) for p in active_platforms)

    # per-source breakdown for email
    source_breakdown: dict[str, int] = {}
    for j in new_jobs:
        src = j.get("source") or j.get("Source") or "Unknown"
        source_breakdown[src] = source_breakdown.get(src, 0) + 1

    source_rows = ""
    for src, cnt in sorted(source_breakdown.items(), key=lambda x: -x[1]):
        source_rows += (
            f"<tr><td style='padding:5px 12px;font-size:13px;color:#555;'>{src}</td>"
            f"<td style='padding:5px 12px;text-align:center;font-size:13px;font-weight:bold;"
            f"color:#1565c0;'>+{cnt}</td></tr>"
        )

    status_color = "#2e7d32" if added > 0 else "#888"
    status_icon = "&#10003;" if added > 0 else "&#8212;"
    status_text = f"+{added} new jobs added" if added > 0 else "No new jobs today"

    html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'></head>
<body style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f5f7fa;padding:20px;'>
  <div style='background:linear-gradient(135deg,#1F3864,#2E75B6);border-radius:12px 12px 0 0;padding:24px 32px;'>
    <h2 style='color:#fff;margin:0;font-size:18px;'>&#128196; job_db loaded &mdash; {today_str}</h2>
    <p style='color:#cde4ff;margin:6px 0 0;font-size:13px;'>France &bull; English-speaking roles &bull; Auto-update</p>
  </div>
  <div style='background:#fff;border:1px solid #e0e0e0;border-top:none;padding:24px 32px;'>

    <!-- Status banner -->
    <div style='background:{"#e8f5e9" if added > 0 else "#f5f5f5"};border-radius:8px;padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;'>
      <span style='font-size:28px;color:{status_color};font-weight:bold;margin-right:12px;'>{status_icon}</span>
      <div>
        <div style='font-size:18px;font-weight:bold;color:{status_color};'>{status_text}</div>
        <div style='font-size:13px;color:#666;margin-top:2px;'>Scanned {len(SEARCH_QUERIES)} queries &bull; Completed in {elapsed:.0f}s</div>
      </div>
    </div>

    <!-- KPI row -->
    <table width='100%' style='border-collapse:collapse;margin-bottom:20px;'>
      <tr>
        <td style='width:33%;text-align:center;background:#e3f2fd;border-radius:8px;padding:14px;'>
          <div style='font-size:26px;font-weight:bold;color:#1565c0;'>+{added}</div>
          <div style='font-size:12px;color:#555;'>New Today</div>
        </td>
        <td style='width:4%;'></td>
        <td style='width:33%;text-align:center;background:#f3e5f5;border-radius:8px;padding:14px;'>
          <div style='font-size:26px;font-weight:bold;color:#6a1b9a;'>{total_after}</div>
          <div style='font-size:12px;color:#555;'>Total in DB</div>
        </td>
        <td style='width:4%;'></td>
        <td style='width:33%;text-align:center;background:#fff3e0;border-radius:8px;padding:14px;'>
          <div style='font-size:26px;font-weight:bold;color:#e65100;'>{total_before}</div>
          <div style='font-size:12px;color:#555;'>Before Today</div>
        </td>
      </tr>
    </table>

    {"<!-- Breakdown table --><h3 style='font-size:14px;color:#333;margin:0 0 8px;'>Breakdown by Role</h3><table width='100%' style='border-collapse:collapse;background:#fafafa;border-radius:8px;overflow:hidden;border:1px solid #e0e0e0;'><tr style='background:#1F3864;'><th style='padding:8px 12px;color:#fff;font-size:13px;text-align:left;'>Role</th><th style='padding:8px 12px;color:#fff;font-size:13px;text-align:center;'>Added</th></tr>" + breakdown_rows + "</table>" if added > 0 else ""}

    {"<h3 style='font-size:13px;color:#555;margin:20px 0 6px;'>By Platform</h3><table width='100%' style='border-collapse:collapse;'>" + source_rows + "</table>" if source_rows else ""}

    <p style='font-size:12px;color:#aaa;margin-top:20px;border-top:1px solid #f0f0f0;padding-top:12px;'>
      Sources: {platforms_str}<br>
      DB: job_applications.xlsx &bull; Powered by Claude Code Job Tracker
    </p>
  </div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"job_db loaded â€” {today_str} | +{added} new jobs (Total: {total_after})"
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
        print(f"  Email sent -> {RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"  [warn] Email failed: {e}")


def main():
    start = time.time()
    banner(f"Job Apply Tracker  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    check_api_key()

    # â”€â”€ Step 1: Load workbook â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n[1/9] Loading workbook...")
    wb, is_new = _load_or_create()
    _ensure_jobs_sheet(wb)
    existing_ids = load_existing_job_ids(wb)
    total_before = len(existing_ids)
    print(f"  Existing jobs in DB: {total_before}")

    # â”€â”€ Step 2: Fetch from Indeed â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n[2/9] Fetching jobs from all platforms for {len(SEARCH_QUERIES)} search queries...")
    all_jobs = fetch_all_jobs()
    print(f"  Total unique jobs fetched: {len(all_jobs)}")

    # â”€â”€ Step 3: Exclude already-tracked jobs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n[3/9] Deduplicating against Excel DB...")
    new_jobs = [j for j in all_jobs if str(j.get("job_id", "")) not in existing_ids]
    print(f"  New (not in DB): {len(new_jobs)}  |  Already in DB: {len(all_jobs) - len(new_jobs)}")

    # â”€â”€ Step 4: Filter English-speaking roles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if new_jobs:
        print("\n[4/9] Classifying for English-speaking requirement (Claude API + cache)...")
        english_jobs = filter_english_jobs(new_jobs)
    else:
        english_jobs = []
        print("\n[4/9] No new jobs to classify.")

    # â”€â”€ Step 5: Update Excel DB â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n[5/9] Writing to Excel DB and rebuilding dashboard...")
    added = append_jobs(wb, english_jobs)
    _build_dashboard(wb)
    save_workbook(wb)
    total_after = total_before + added

    # â”€â”€ Step 6: Sync Chrome bookmarks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n[6/9] Syncing Chrome 'Jobs' bookmarks folder...")
    sync_bookmarks(verbose=True)

    # â”€â”€ Step 7: Sync cloud DB + push notification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n[7/9] Syncing cloud DB (Telegraph)...")
    telegraph_url = sync_cloud(added, total_after, verbose=True)

    # â”€â”€ Step 8: Sync Excel to Google Drive â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n[8/9] Uploading to Google Drive...")
    sync_gdrive(verbose=True)

    # â”€â”€ Step 9: Send DB update email â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elapsed = time.time() - start
    print("\n[9/9] Sending job_db update email...")
    send_db_update_email(added, total_before, total_after, english_jobs, elapsed)

    # â”€â”€ Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    banner("Run Complete")
    print(f"  Queries run       : {len(SEARCH_QUERIES)}")
    print(f"  Jobs fetched      : {len(all_jobs)}")
    print(f"  New English jobs  : {len(english_jobs)}")
    print(f"  Added to DB       : {added}")
    print(f"  Total in DB       : {total_after}")
    print(f"  Output file       : {OUTPUT_PATH}")
    print(f"  Elapsed           : {elapsed:.1f}s")
    print()


if __name__ == "__main__":
    main()
