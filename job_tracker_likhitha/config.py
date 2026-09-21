import os

# ── Search parameters ──────────────────────────────────────────────────────────
SEARCH_QUERIES = [
    "Project Manager",
    "Scrum Master",
    "Agile Project Manager",
    "Program Manager",
    "Delivery Manager",
]

LOCATION      = "France"
COUNTRY_CODE  = "FR"   # ISO-2

# ── English filter ─────────────────────────────────────────────────────────────
ENGLISH_CONFIDENCE_THRESHOLD = 0.75

# ── Retention window ───────────────────────────────────────────────────────────
# Job listings age out fast — a 5-week-old "Saved" posting is very likely
# expired or filled. Every run prunes Saved rows older than this many days
# from both the Excel DB and (since Telegraph mirrors the Excel DB) the
# Telegraph page — this also keeps the page under Telegraph's size limit.
# Rows already acted on (Applied/Interview/Offer/Rejected) are never
# pruned by age — that's real application history, not stale listing noise.
JOB_RETENTION_DAYS = 28  # ~4 weeks (requested window: 3-4 weeks)

# ── Output ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "outputs")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "job_applications_likhitha.xlsx")

# ── Claude model (haiku = cheapest, fast enough for classification) ────────────
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# ── Status choices for Excel dropdown ─────────────────────────────────────────
STATUS_CHOICES = ["Saved", "Applied", "Interview", "Offer", "Rejected"]

# ── Platform API credentials (read from .env) ──────────────────────────────────
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
