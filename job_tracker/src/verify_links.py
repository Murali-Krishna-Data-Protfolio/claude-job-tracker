"""
verify_links.py — Check every Apply_URL already in the tracker and drop rows
whose listing is dead: expired, removed, 404/410, or the host is unreachable.

Pure HTTP checks, no Claude API involved — unaffected by ANTHROPIC_API_KEY /
org status, unlike reclassify_legacy.py. Uses a thread pool since checking
hundreds of URLs one at a time would be slow (this is I/O-bound, not
CPU-bound). Always makes a timestamped backup of the workbook before writing
anything.

Usage:
    python verify_links.py                  # dry run — report scope only, no requests, no writes
    python verify_links.py --apply           # actually check every link and rewrite the sheet
    python verify_links.py --apply --workers 20
"""

import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from config import OUTPUT_PATH
from excel_writer import _build_dashboard, rewrite_jobs_sheet, save_workbook
from job_fetcher import check_url

# Job titles/companies are full of accented French text; some terminals
# default stdout to cp1252, which crashes on encode instead of just failing
# to render the glyph. Never let a print() kill a run mid-way through a
# destructive operation.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


def _get_rows(ws):
    header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    rows = []
    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if row[0]:
            rows.append((row_num, dict(zip(header, row))))
    return rows


def main():
    apply = "--apply" in sys.argv
    workers = 15
    if "--workers" in sys.argv:
        i = sys.argv.index("--workers")
        if i + 1 < len(sys.argv):
            workers = int(sys.argv[i + 1])

    if not Path(OUTPUT_PATH).exists():
        print(f"[ERROR] No tracker found at {OUTPUT_PATH}")
        sys.exit(1)

    wb = load_workbook(OUTPUT_PATH)
    ws = wb["Jobs"]
    rows = _get_rows(ws)
    total = len(rows)

    print(f"Tracker: {OUTPUT_PATH}")
    print(f"Total jobs: {total}")

    if not apply:
        print(f"\nDry run — would check {total} URLs with {workers} concurrent workers.")
        print("No requests made, nothing written. Re-run with --apply to actually check and rewrite.")
        return

    print(f"\nChecking {total} links with {workers} workers (this can take a few minutes)...")

    def _check(item):
        row_num, r = item
        ok, reason = check_url(r.get("Apply_URL", "") or "")
        return row_num, r, ok, reason

    results: dict[int, tuple[bool, str]] = {}
    checked = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_check, item) for item in rows]
        for fut in as_completed(futures):
            row_num, r, ok, reason = fut.result()
            results[row_num] = (ok, reason)
            checked += 1
            if not ok or checked % 25 == 0:
                verdict = "PASS" if ok else "DEAD"
                print(f"  [{checked}/{total}] {verdict} row {row_num}: {r.get('Title')} @ {r.get('Company')} — {reason}")

    dead = sorted(rn for rn, (ok, _) in results.items() if not ok)
    alive = total - len(dead)

    print(f"\nValid links: {alive} / {total}")
    print(f"Dead links (to be removed — 404/410 only): {len(dead)}")

    if not dead:
        print("Nothing to remove.")
        return

    backup_path = Path(OUTPUT_PATH).with_name(
        f"{Path(OUTPUT_PATH).stem}.backup-{datetime.now():%Y%m%d-%H%M%S}.xlsx"
    )
    shutil.copy2(OUTPUT_PATH, backup_path)
    print(f"Backup saved: {backup_path}")

    dead_set = set(dead)
    keep_rows = [r for rn, r in rows if rn not in dead_set]
    rewrite_jobs_sheet(wb, keep_rows)

    _build_dashboard(wb)
    save_workbook(wb)

    print(f"\nDone. Removed {len(dead)} dead links. {alive} valid jobs remain.")
    print(f"Tracker: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
