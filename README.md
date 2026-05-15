# Murali Krishna — Job Tracker

**MSc Data Science & Business Analytics | EDC Paris | France**  
Target roles: Data Analyst · Data Engineer · Business Analyst · BI Developer · Analytics Engineer

---

## What it does

Every weekday at **08:00 Paris time**, the system automatically:

1. Searches **Adzuna + France Travail** for Data/Analytics roles in France
2. Filters with **Claude AI** — keeps only English-speaking workplaces
3. Appends new jobs to **`job_applications.xlsx`** (no duplicates)
4. Updates the **live cloud page** (mobile-readable, tap to apply)
5. Sends a **push notification** via ntfy app
6. Emails a digest to **gkmurali37@gmail.com**
7. Uploads the Excel to **Google Drive**

---

## Quick start

```powershell
cd C:\Claude\job_tracker
python job_tracker.py        # run now manually
```

---

## Folder structure

```
C:\Claude\
├── README.md                          ← this file
│
├── job_tracker\
│   ├── job_tracker.py                 ← main pipeline (run this daily)
│   ├── job_fetcher.py                 ← fetches jobs + Claude English filter
│   ├── excel_writer.py                ← builds Jobs sheet + Dashboard charts
│   ├── config.py                      ← search queries, platforms, thresholds
│   ├── profile_cache.py               ← Claude prompt cache (saves ~65% tokens)
│   ├── sync_cloud.py                  ← Telegraph live page + ntfy push
│   ├── sync_gdrive.py                 ← Google Drive upload
│   ├── sync_bookmarks.py              ← Chrome bookmarks sync
│   ├── write_jobs.py                  ← CLI helper: python write_jobs.py file.json
│   ├── run_daily.bat                  ← Task Scheduler entry point
│   ├── setup_scheduler.ps1            ← register 08:00 daily task (run once as Admin)
│   ├── requirements.txt               ← pip install -r requirements.txt
│   ├── .env                           ← API keys (never share)
│   ├── .env.example                   ← key template for new machines
│   └── outputs\
│       └── job_applications.xlsx      ← live Excel tracker + dashboard
│
└── resumes\
    ├── generate_resumes.py            ← generates all 4 role PDFs
    ├── gen_ae_de.py                   ← Analytics Engineer + Data Engineer only
    ├── Profile.pdf                    ← source profile (update → re-run generator)
    └── output\
        ├── Resume_DataAnalyst_MuraliKrishna.pdf
        ├── Resume_DataEngineer_MuraliKrishna.pdf
        ├── Resume_BusinessAnalyst_MuraliKrishna.pdf
        └── Resume_AnalyticsEngineer_MuraliKrishna.pdf
```

---

## Job platforms

| Platform | What it covers | Key needed |
|---|---|---|
| **Adzuna** | Aggregates APEC, Monster, Cadremploi, RegionsJob + 10 more | Free — [developer.adzuna.com](https://developer.adzuna.com/signup) ✅ set |
| **Indeed** | Cloud CCR routine only (via MCP tool) | None ✅ (cloud only) |
| JSearch (LinkedIn + Glassdoor) | LinkedIn Jobs + Glassdoor via RapidAPI | Free — [rapidapi.com → JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) |

> Indeed works only in the cloud CCR routine (uses MCP tool). It does not run locally.  
> To unlock LinkedIn/Glassdoor: subscribe to JSearch free tier on RapidAPI — your key is already in `.env`.

---

## Mobile access

### Live job DB (no login, any browser)
**[telegra.ph/Murali-Job-DB-France-05-15](https://telegra.ph/Murali-Job-DB-France-05-15)**  
Updated every morning. Tap any title to open the apply link.

### Push notifications
1. Install **ntfy** app (iOS / Android — free, no account)
2. Subscribe to topic: **`murali_jobs_24c68f94`**

### Google Drive (Excel on mobile)
After setup (below), `job_applications.xlsx` auto-uploads to your Drive.  
Open with **Google Sheets** on mobile to filter, sort, and tap apply links.

---

## Excel tracker

| Sheet | Contents |
|---|---|
| **Jobs** | Every job found — Title, Company, Location, Salary, Status, URL, Source, Date |
| **Dashboard** | Charts — Jobs by Role, Status breakdown, New jobs per day, Top Companies |

Update **Status** as you apply:
```
Saved → Applied → Interview → Offer
                → Rejected
```

---

## Daily automation

### Cloud routine (runs even when PC is off)
- **Link:** [claude.ai/code/routines/trig_014b4yLVQDgTbrVmQTcb1ymi](https://claude.ai/code/routines/trig_014b4yLVQDgTbrVmQTcb1ymi)
- Schedule: every weekday **08:00 Paris time** (06:00 UTC)
- Uses Indeed MCP → fetches + filters → Excel → email + push

### Local Task Scheduler (runs on this PC)
Run **once as Administrator**:
```powershell
powershell -ExecutionPolicy Bypass -File C:\Claude\job_tracker\setup_scheduler.ps1
```

---

## Setup (one-time steps)

### Google Drive
1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create project → **APIs & Services → Library** → enable **Google Drive API**
3. **Credentials → OAuth client ID** → Desktop app → download JSON
4. Rename to `credentials.json` → place in `C:\Claude\job_tracker\`
5. Run once (browser opens for sign-in):
   ```bat
   cd C:\Claude\job_tracker && python sync_gdrive.py --setup
   ```

### Reset cloud page / ntfy topic
```bat
cd C:\Claude\job_tracker && python sync_cloud.py --setup
```

### Add LinkedIn + Glassdoor
Subscribe to **JSearch** (free, 200 req/month):
1. Go to [rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)
2. Click **Subscribe to Test → Basic (Free)**
3. Done — your key in `.env` works automatically

---

## Environment variables (`.env`)

| Variable | Purpose | Status |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude AI — English filter + resume generation | ✅ set |
| `GMAIL_APP_PASSWORD` | Daily digest email | ✅ set |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | Adzuna job aggregator | ✅ set |
| `RAPIDAPI_KEY` | LinkedIn + Glassdoor (needs JSearch subscription) | ✅ set (subscribe JSearch) |
| `TELEGRAPH_ACCESS_TOKEN` | Live page auth (auto-set) | ✅ set |
| `TELEGRAPH_PAGE_PATH` | Live page ID (auto-set) | ✅ set |
| `NTFY_TOPIC` | Push notification topic (auto-set) | ✅ set |
| `GDRIVE_FOLDER_ID` / `GDRIVE_FILE_ID` | Drive file IDs (auto-set after setup) | ⬜ run setup |

---

## Resume generator

```powershell
cd C:\Claude\resumes
python generate_resumes.py     # all 4 roles
python gen_ae_de.py            # Analytics Engineer + Data Engineer only
```

Update `resumes\Profile.pdf` first whenever your profile changes, then re-run.

---

## Common commands

| What | Command |
|---|---|
| Run job search now | `cd C:\Claude\job_tracker && python job_tracker.py` |
| Force update cloud page | `python C:\Claude\job_tracker\sync_cloud.py` |
| Force upload to Google Drive | `python C:\Claude\job_tracker\sync_gdrive.py` |
| Sync Chrome bookmarks only | `python C:\Claude\job_tracker\sync_bookmarks.py` |
| Generate resumes | `cd C:\Claude\resumes && python generate_resumes.py` |
| Install dependencies | `pip install -r C:\Claude\job_tracker\requirements.txt` |
| Open Excel tracker | `C:\Claude\job_tracker\outputs\job_applications.xlsx` |
