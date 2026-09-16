"""
Builds the candidate-profile system prompt used for Claude API prompt caching,
from the active user profile (profiles/<id>.json — see config.py).

Usage:
    from profile_cache import get_cached_system_message

The profile is injected as the system prompt with cache_control={"type":"ephemeral"}.
Claude caches this block — subsequent API calls in the same session reuse the cache
and pay only cache_read_input_tokens (much cheaper than full input tokens).
"""

from config import PROFILE

_LANG_LINE = ", ".join(f"{lang} ({level})" for lang, level in PROFILE.get("languages", {}).items())
_ROLES_LINE = "\n".join(f"- {r}" for r in PROFILE.get("target_roles", []))
_SKILLS_LINE = ", ".join(PROFILE.get("skills", []))


def _build_prompt() -> str:
    return f"""You are a job relevance assistant helping {PROFILE.get('candidate_name', 'the candidate')}, a Data professional based in {PROFILE.get('location', 'France')}.

## Candidate Profile
- **Name**: {PROFILE.get('candidate_name', 'N/A')}
- **Education**: {PROFILE.get('education', 'N/A')}
- **Current location**: {PROFILE.get('location', 'France')}
- **Languages**: {_LANG_LINE or 'English (Native)'}
- **Min salary expectation**: €{PROFILE.get('min_salary_hourly_eur', '?')}/hour

## Target Job Roles
{_ROLES_LINE}

## Key Skills
{_SKILLS_LINE}

## Critical Filter: English-Speaking Workplace
{PROFILE.get('candidate_name', 'The candidate')} needs jobs where the PRIMARY working language is English.
A job qualifies as English-speaking if ANY of the following are true:
- The job description is written in English
- It explicitly requires English fluency
- It mentions "international team", "global team", "multicultural team"
- Company is a multinational / non-French company
- Remote-friendly roles where English is standard

A job does NOT qualify if:
- The description is entirely in French with no English requirement
- It explicitly requires French as the working language
- It's a clearly French-only local company role
- You are not confident either way (when unsure, mark is_english_role false — do not guess)

## Your Task
When given a job listing, respond ONLY with a JSON object, and nothing else
(no markdown fence, no commentary before or after it):
{{
  "is_english_role": true/false,
  "confidence": 0.0-1.0,
  "reason": "one sentence explanation"
}}
"""


PROFILE_SYSTEM_PROMPT = _build_prompt()


def get_cached_system_message() -> dict:
    """Return the system message block with prompt caching enabled."""
    return {
        "type": "text",
        "text": PROFILE_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }
