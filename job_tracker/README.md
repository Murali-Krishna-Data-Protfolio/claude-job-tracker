# Job Apply Tracker

Automated daily job search: fetches Data/Analytics roles, keeps **only
verified English-speaking-workplace listings**, and writes them into a
BI-ready Excel tracker — with optional Chrome bookmarks, Google Drive,
Telegraph (mobile page), and email-digest sync.

Built around one **candidate profile per user** — no source code changes
needed to run this for someone else. See [Add another user](#add-another-user).

## Project layout

```
job_tracker/
├── src/                      # all source code, centralized here
│   ├── job_tracker.py        #   main pipeline — run this daily
│   ├── job_fetcher.py        #   multi-platform fetch + English classifier
│   ├── excel_writer.py       #   Jobs sheet + Dashboard/charts (openpyxl)
│   ├── profile_cache.py      #   builds the Claude system prompt from the active profile
│   ├── config.py             #   loads .env + the active profile
│   ├── sync_bookmarks.py     #   Chrome "Jobs" bookmarks folder
│   ├── sync_cloud.py         #   Telegraph mobile page + ntfy push
│   ├── sync_gdrive.py        #   Google Drive upload
│   └── write_jobs.py         #   entry point for the cloud/MCP (Indeed) route
├── profiles/
│   ├── example.json          # template — copy this for a new user
│   └── murali.json           # a real profile
├── outputs/
│   ├── run_log.txt           # shared scheduler log
│   └── <profile_id>/job_applications.xlsx   # one tracker per profile
├── .env                       # secrets (gitignored) — API keys, Gmail login
├── .env.example                # template for .env
├── run_daily.bat               # Task Scheduler entry point
└── setup_scheduler.ps1         # registers the daily Task Scheduler job
```

## How the pipeline works

See **[docs/data-workflow.html](docs/data-workflow.html)** for the full
diagram. In short, `src/job_tracker.py` runs a 9-step pipeline:

1. Load the Excel tracker (`outputs/<profile>/job_applications.xlsx`)
2. Fetch jobs from every enabled platform (Adzuna, JSearch, Indeed via cloud MCP, …)
3. Drop anything already in the tracker (dedup by `job_id`)
4. **Classify each new job with Claude** — English-speaking-workplace or not
5. Append the passing jobs, rebuild the Dashboard sheet, save
6. Sync the Chrome "Jobs" bookmarks folder
7. Push the mobile Telegraph page + ntfy notification
8. Upload the Excel file to Google Drive
9. Email a run summary

## The English filter is strict / fail-closed

A job is added **only** when Claude confirms `is_english_role: true` with
confidence ≥ the profile's threshold (default `0.75`). If the API call
errors, the response can't be parsed, or the model isn't confident — the
job is **excluded**, never guessed in. Nothing gets into the tracker
without being verified.

(This used to fail *open*: a parsing bug meant ~83% of classifier calls
silently defaulted to "included" regardless of the actual verdict, which is
how French-only listings were leaking in. Fixed in `src/job_fetcher.py` —
see `_extract_json_object()`.)

## Quickstart (existing profile)

```bash
pip install -r requirements.txt
cd src
python job_tracker.py
```

## Add another user

1. Copy `profiles/example.json` → `profiles/<your_id>.json` and fill in your
   name, education, location, target roles, skills, salary floor, and
   notification email.
2. Copy `.env.example` → `.env`, add your own `ANTHROPIC_API_KEY`,
   `GMAIL_USER` + `GMAIL_APP_PASSWORD` (a
   [Gmail App Password](https://myaccount.google.com/apppasswords), not your
   real password), and optionally `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` or
   `RAPIDAPI_KEY` to unlock more job sources.
3. Set `ACTIVE_PROFILE=<your_id>` in `.env`.
4. `cd src && python job_tracker.py`

Your tracker is written to `outputs/<your_id>/job_applications.xlsx`,
completely separate from any other profile's data.

## Daily automation (Windows Task Scheduler)

```powershell
powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1
```

Registers a task that runs `run_daily.bat` every day at 08:00, which in turn
runs `src\job_tracker.py` and appends to `outputs\run_log.txt`.

## Optional one-time setups

```bash
cd src
python sync_cloud.py --setup     # Telegraph page + ntfy push topic
python sync_gdrive.py --setup    # Google Drive OAuth + folder
```
