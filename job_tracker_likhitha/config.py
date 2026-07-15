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
