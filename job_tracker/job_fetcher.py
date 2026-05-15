"""
Multi-platform job fetcher for English-speaking roles in France.

Sources (all free, keys optional):
  1. Indeed             – HTTP scraping         (no key)
  2. Welcome to the     – JSON API              (no key)
     Jungle (WTTJ)
  3. Talent.io          – JSON API              (no key)
  4. France Travail     – server-side HTML      (no key)
                          (ex-Pôle Emploi, official FR board)
  5. Adzuna             – Official free API     (ADZUNA_APP_ID + ADZUNA_APP_KEY)
  6. JSearch            – RapidAPI free tier    (RAPIDAPI_KEY)
                          covers LinkedIn Jobs + Glassdoor

Add keys to .env to unlock more sources.
"""

import hashlib
import json
import os
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

import anthropic

from config import (
    ADZUNA_APP_ID, ADZUNA_APP_KEY,
    CLAUDE_MODEL,
    COUNTRY_CODE,
    ENGLISH_CONFIDENCE_THRESHOLD,
    LOCATION,
    PLATFORMS,
    RAPIDAPI_KEY,
    SEARCH_QUERIES,
)
from profile_cache import get_cached_system_message

# ── Shared HTTP headers ────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_id(title: str, company: str, source: str) -> str:
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{source}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _norm(job: dict, source: str, query: str) -> dict:
    """Normalise a raw job dict to the standard schema."""
    title   = str(job.get("title",   "")).strip()
    company = str(job.get("company", "")).strip()
    return {
        "job_id":      job.get("job_id") or _make_id(title, company, source),
        "title":       title,
        "company":     company,
        "location":    str(job.get("location", LOCATION)).strip(),
        "salary":      job.get("salary") or None,
        "url":         job.get("url", ""),
        "description": (job.get("description") or "")[:500],
        "source":      source,
        "search_query": query,
    }


def _get(url: str, params: dict | None = None,
         headers: dict | None = None, timeout: int = 15) -> requests.Response | None:
    try:
        r = requests.get(url, params=params,
                         headers=headers or HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r
    except requests.RequestException as e:
        print(f"    [warn] GET {url[:60]}: {e}")
    return None


# ── 1. Indeed ─────────────────────────────────────────────────────────────────

def _fetch_indeed(query: str) -> list[dict]:
    jobs = []
    for base in ["https://fr.indeed.com", "https://www.indeed.com"]:
        r = _get(f"{base}/jobs",
                 params={"q": query, "l": "France", "lang": "en", "radius": "50"})
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        cards = (soup.select("div.job_seen_beacon")
                 or soup.select("div.result")
                 or soup.select("td.resultContent"))
        for card in cards:
            try:
                t = card.select_one("h2.jobTitle span[title]") or card.select_one("h2.jobTitle")
                c = card.select_one("[data-testid='company-name']") or card.select_one(".companyName")
                lo = card.select_one("[data-testid='text-location']") or card.select_one(".companyLocation")
                s  = card.select_one(".salary-snippet-container") or card.select_one(".salaryText")
                a  = card.select_one("h2.jobTitle a") or card.select_one("a.jcs-JobTitle")
                d  = card.select_one("div.job-snippet")
                title   = t.get_text(strip=True) if t else ""
                company = c.get_text(strip=True) if c else ""
                if not title or not company:
                    continue
                href    = a.get("href", "") if a else ""
                job_url = (base + href) if href.startswith("/") else href
                jobs.append(_norm({
                    "title":   title, "company": company,
                    "location": lo.get_text(strip=True) if lo else "France",
                    "salary":  s.get_text(strip=True) if s else None,
                    "url":     job_url,
                    "description": d.get_text(" ", strip=True) if d else "",
                }, "Indeed", query))
            except Exception:
                continue
        if jobs:
            break
    return jobs


# ── 2. Welcome to the Jungle ──────────────────────────────────────────────────

def _fetch_wttj(query: str) -> list[dict]:
    """WTTJ public JSON API – English jobs in France."""
    jobs = []
    # Try their internal API endpoint
    r = _get(
        "https://api.welcometothejungle.com/api/v1/jobs",
        params={
            "query": query, "page": 1, "per_page": 30,
            "country_code": "FR", "language": "en",
        },
        headers={**HEADERS, "Accept": "application/json"},
    )
    if r:
        try:
            data = r.json()
            items = data.get("jobs") or data.get("results") or []
            for item in items:
                org = item.get("organization") or {}
                jobs.append(_norm({
                    "title":       item.get("name", ""),
                    "company":     org.get("name", ""),
                    "location":    (item.get("office", {}) or {}).get("city", "France"),
                    "salary":      None,
                    "url":         f"https://www.welcometothejungle.com{item.get('reference', '')}",
                    "description": item.get("description_plain", "")[:500],
                }, "WelcomeToTheJungle", query))
            if jobs:
                return jobs
        except (json.JSONDecodeError, AttributeError):
            pass

    # Fallback: scrape HTML search page
    r = _get(
        "https://www.welcometothejungle.com/en/jobs",
        params={"query": query, "where": "France", "refinementList[contract_type_names.en][]": "Full-Time"},
    )
    if r:
        soup = BeautifulSoup(r.text, "lxml")
        for card in soup.select("li[data-testid='search-results-list-item-wrapper']")[:15]:
            try:
                t = card.select_one("h3") or card.select_one("[data-testid='job-title']")
                c = card.select_one("[data-testid='company-name']") or card.select_one("span.sc-bHwgHz")
                lo = card.select_one("[data-testid='job-location']")
                a  = card.select_one("a[href*='/jobs/']")
                if not (t and c):
                    continue
                href = a.get("href", "") if a else ""
                jobs.append(_norm({
                    "title":    t.get_text(strip=True),
                    "company":  c.get_text(strip=True),
                    "location": lo.get_text(strip=True) if lo else "France",
                    "url": ("https://www.welcometothejungle.com" + href) if href.startswith("/") else href,
                    "description": "",
                }, "WelcomeToTheJungle", query))
            except Exception:
                continue
    return jobs


# ── 3. Talent.io ──────────────────────────────────────────────────────────────

def _fetch_talentio(query: str) -> list[dict]:
    """Talent.io – tech/data jobs in France, many English-speaking."""
    jobs = []
    # Talent.io GraphQL / REST endpoint
    r = _get(
        "https://api.talent.io/api/v1/jobs",
        params={
            "search": query, "countryCode": "FR",
            "contractTypes": "full_time", "page": 1,
        },
        headers={**HEADERS, "Accept": "application/json"},
    )
    if r:
        try:
            data = r.json()
            items = data.get("jobs") or data.get("data") or []
            for item in items:
                company_info = item.get("company") or {}
                jobs.append(_norm({
                    "title":       item.get("title", ""),
                    "company":     company_info.get("name", ""),
                    "location":    (item.get("location") or {}).get("city", "France"),
                    "salary":      _fmt_salary(item.get("salary")),
                    "url":         f"https://www.talent.io/p/en-fr/jobs/{item.get('slug', '')}",
                    "description": item.get("description", "")[:500],
                }, "Talent.io", query))
            if jobs:
                return jobs
        except (json.JSONDecodeError, AttributeError):
            pass

    # Fallback: scrape public search page
    r = _get(
        "https://www.talent.io/p/en-fr/jobs",
        params={"q": query, "location": "France"},
    )
    if r:
        soup = BeautifulSoup(r.text, "lxml")
        for card in soup.select("div.JobCard, article.job-card, div[class*='JobItem']")[:15]:
            try:
                t = card.select_one("h2, h3, [class*='title']")
                c = card.select_one("[class*='company'], [class*='employer']")
                a = card.select_one("a[href*='/jobs/']")
                if not (t and c):
                    continue
                href = a.get("href", "") if a else ""
                jobs.append(_norm({
                    "title":   t.get_text(strip=True),
                    "company": c.get_text(strip=True),
                    "url": ("https://www.talent.io" + href) if href.startswith("/") else href,
                }, "Talent.io", query))
            except Exception:
                continue
    return jobs


def _fmt_salary(s: Any) -> str | None:
    if not s:
        return None
    if isinstance(s, dict):
        mn = s.get("min") or s.get("minimum")
        mx = s.get("max") or s.get("maximum")
        curr = s.get("currency", "EUR")
        if mn and mx:
            return f"{mn:,}–{mx:,} {curr}"
        if mn:
            return f"From {mn:,} {curr}"
    return str(s) if s else None


# ── 4. France Travail (ex-Pôle Emploi) ───────────────────────────────────────
# candidat.francetravail.fr — official French government job board, server-side HTML

_FT_BASE = "https://candidat.francetravail.fr"

def _fetch_francetravail(query: str) -> list[dict]:
    """Scrape France Travail search results (server-side rendered, no key needed)."""
    jobs = []
    r = _get(
        f"{_FT_BASE}/offres/recherche",
        params={"motsCles": query, "lieuId": "FR", "nbrParPage": 20, "page": 1},
        headers={**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"},
    )
    if not r:
        return []
    soup = BeautifulSoup(r.text, "lxml")
    for item in soup.select("li.result"):
        try:
            job_id = item.get("data-id-offre", "")
            title_el = item.select_one("span.media-heading-title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue
            subtext = item.select_one("p.subtext")
            company  = ""
            location = "France"
            if subtext:
                # subtext format: "COMPANY NAME - <span>CITY - DEPT</span>"
                # Extract company from direct text nodes (exclude span)
                location_span = subtext.select_one("span")
                if location_span:
                    location = location_span.get_text(strip=True)
                    location_span.extract()   # remove span temporarily
                company = subtext.get_text(strip=True).strip(" -")
            desc_el = item.select_one("p.description")
            href = (item.select_one("a.media") or {}).get("href", "") if item.select_one("a.media") else ""
            url = (_FT_BASE + href) if href.startswith("/") else href
            jobs.append(_norm({
                "job_id":      job_id,
                "title":       title,
                "company":     company,
                "location":    location,
                "url":         url,
                "description": desc_el.get_text(" ", strip=True) if desc_el else "",
            }, "FranceTravail", query))
        except Exception:
            continue
    return jobs


# ── 5. Adzuna ─────────────────────────────────────────────────────────────────
# Covers: APEC, Monster France, Cadremploi, RegionsJob, and 10+ more

def _fetch_adzuna(query: str) -> list[dict]:
    if not (ADZUNA_APP_ID and ADZUNA_APP_KEY):
        return []
    jobs = []
    r = _get(
        "https://api.adzuna.com/v1/api/jobs/fr/search/1",
        params={
            "app_id": ADZUNA_APP_ID, "app_key": ADZUNA_APP_KEY,
            "results_per_page": 20,
            "what": query,
            "where": "france",
            "content-type": "application/json",
            "sort_by": "date",
            "max_days_old": 14,
        },
    )
    if not r:
        return []
    try:
        data = r.json()
        for item in data.get("results", []):
            company = (item.get("company") or {}).get("display_name", "")
            location = (item.get("location") or {}).get("display_name", "France")
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary_str = None
            if salary_min and salary_max:
                salary_str = f"{int(salary_min):,}–{int(salary_max):,} EUR"
            elif salary_min:
                salary_str = f"From {int(salary_min):,} EUR"
            jobs.append(_norm({
                "job_id":      item.get("id", ""),
                "title":       item.get("title", ""),
                "company":     company,
                "location":    location,
                "salary":      salary_str,
                "url":         item.get("redirect_url", ""),
                "description": item.get("description", "")[:500],
            }, "Adzuna", query))
    except (json.JSONDecodeError, KeyError):
        pass
    return jobs


# ── 6. JSearch (RapidAPI) – LinkedIn + Glassdoor ──────────────────────────────

def _fetch_jsearch(query: str) -> list[dict]:
    if not RAPIDAPI_KEY:
        return []
    jobs = []
    r = _get(
        "https://jsearch.p.rapidapi.com/search",
        params={
            "query":     f"{query} in France",
            "num_pages": "1",
            "language":  "en",
            "country":   "fr",
        },
        headers={
            "X-RapidAPI-Key":  RAPIDAPI_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        },
    )
    if not r:
        return []
    try:
        for item in r.json().get("data", []):
            salary_str = None
            smin = item.get("job_min_salary")
            smax = item.get("job_max_salary")
            scurr = item.get("job_salary_currency", "EUR")
            if smin and smax:
                salary_str = f"{int(smin):,}–{int(smax):,} {scurr}"
            publisher = item.get("job_publisher", "")   # "LinkedIn", "Glassdoor", etc.
            source_label = publisher if publisher else "JSearch"
            jobs.append(_norm({
                "job_id":      item.get("job_id", ""),
                "title":       item.get("job_title", ""),
                "company":     item.get("employer_name", ""),
                "location":    f"{item.get('job_city','')}, {item.get('job_country','')}".strip(", "),
                "salary":      salary_str,
                "url":         item.get("job_apply_link") or item.get("job_google_link", ""),
                "description": item.get("job_description", "")[:500],
            }, source_label, query))
    except (json.JSONDecodeError, KeyError):
        pass
    return jobs


# ── Aggregator ────────────────────────────────────────────────────────────────

def fetch_all_jobs() -> list[dict]:
    """Fetch from all enabled platforms and deduplicate by job_id."""
    seen:     set[str]  = set()
    all_jobs: list[dict] = []
    source_counts: dict[str, int] = {}

    fetchers = []
    if PLATFORMS.get("indeed"):          fetchers.append(("Indeed",          _fetch_indeed))
    if PLATFORMS.get("wttj"):            fetchers.append(("WelcomeToJungle", _fetch_wttj))
    if PLATFORMS.get("talentio"):        fetchers.append(("Talent.io",       _fetch_talentio))
    if PLATFORMS.get("francetravail"):   fetchers.append(("FranceTravail",   _fetch_francetravail))
    if PLATFORMS.get("adzuna"):          fetchers.append(("Adzuna",          _fetch_adzuna))
    if PLATFORMS.get("jsearch"):         fetchers.append(("JSearch",         _fetch_jsearch))

    active = [name for name, _ in fetchers]
    print(f"  Active sources: {', '.join(active)}")

    for query in SEARCH_QUERIES:
        print(f"\n  [{query}]")
        for source_name, fn in fetchers:
            try:
                results = fn(query)
            except Exception as e:
                print(f"    {source_name}: ERROR – {e}")
                results = []

            new = 0
            for job in results:
                jid = job["job_id"]
                if jid not in seen:
                    seen.add(jid)
                    all_jobs.append(job)
                    source_counts[job["source"]] = source_counts.get(job["source"], 0) + 1
                    new += 1

            print(f"    {source_name}: {len(results)} results, {new} unique new")
            time.sleep(0.8)   # polite between platform calls

    print(f"\n  Total unique jobs: {len(all_jobs)}")
    print("  Per source: " + " | ".join(f"{s}:{n}" for s, n in sorted(source_counts.items())))
    return all_jobs


# ── English-role classifier ───────────────────────────────────────────────────

def filter_english_jobs(jobs: list[dict]) -> list[dict]:
    """Classify each job using Claude API with cached profile prompt."""
    if not jobs:
        return []

    client      = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    cache_block = get_cached_system_message()
    english_jobs: list[dict] = []

    print(f"\n  Classifying {len(jobs)} jobs for English-speaking requirement...")

    for job in jobs:
        job_text = (
            f"Title: {job.get('title','')}\n"
            f"Company: {job.get('company','')}\n"
            f"Location: {job.get('location','')}\n"
            f"Source: {job.get('source','')}\n"
            f"Description: {job.get('description','')}"
        )
        try:
            resp = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=256,
                system=[cache_block],
                messages=[{"role": "user", "content": job_text}],
            )
            raw = re.sub(r"^```[a-z]*\n?|\n?```$", "", resp.content[0].text.strip())
            result     = json.loads(raw)
            confidence = float(result.get("confidence", 0))
            is_english = bool(result.get("is_english_role", False))
            reason     = result.get("reason", "")

            job["english_confidence"] = round(confidence, 2)
            job["english_reason"]     = reason

            cache_hit = getattr(resp.usage, "cache_read_input_tokens", 0)
            tag = f" [cache:{cache_hit}tk]" if cache_hit else ""
            verdict = "PASS" if (is_english and confidence >= ENGLISH_CONFIDENCE_THRESHOLD) else "SKIP"
            src = job.get("source", "")
            print(f"    {verdict} [{src}] {job.get('title')} @ {job.get('company')} ({confidence:.0%}){tag}")

            if is_english and confidence >= ENGLISH_CONFIDENCE_THRESHOLD:
                english_jobs.append(job)

        except (json.JSONDecodeError, ValueError, Exception) as e:
            job["english_confidence"] = 0.5
            job["english_reason"]     = f"parse error: {e}"
            english_jobs.append(job)

    print(f"\n  English-speaking: {len(english_jobs)} / {len(jobs)}")
    return english_jobs
