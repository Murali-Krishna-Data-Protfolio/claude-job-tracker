"""
Gmail Application Tracker
Connects to Gmail via IMAP and checks email threads with a target address
to determine whether an application was submitted and what the response was.

Usage:
    python gmail_application_tracker.py
    python gmail_application_tracker.py --sender sp-etrangers-sarcelles@val-doise.gouv.fr
"""

import argparse
import email
import email.message
import imaplib
import os
import re
import sys
from datetime import datetime
from email.header import decode_header
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass

# ── Credentials ────────────────────────────────────────────────────────────────
GMAIL_USER = "gkmurali37@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "dfzuaeyaehqanfqg")

# ── Target ─────────────────────────────────────────────────────────────────────
DEFAULT_TARGET = "sp-etrangers-sarcelles@val-doise.gouv.fr"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _decode_str(raw) -> str:
    if raw is None:
        return ""
    parts = decode_header(raw)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def _get_body(msg: email.message.Message) -> str:
    body_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                body_parts.append(payload.decode(charset, errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or "utf-8"
        if payload:
            body_parts.append(payload.decode(charset, errors="replace"))
    return "\n".join(body_parts).strip()


def _search_folder(imap: imaplib.IMAP4_SSL, folder: str, criteria: str):
    try:
        status, _ = imap.select(folder, readonly=True)
        if status != "OK":
            return []
        status, data = imap.search(None, criteria)
        if status != "OK" or not data[0]:
            return []
        return data[0].split()
    except Exception:
        return []


def _fetch_messages(imap: imaplib.IMAP4_SSL, ids: list) -> list[dict]:
    messages = []
    for msg_id in ids:
        try:
            status, data = imap.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue
            raw = data[0][1]
            msg = email.message_from_bytes(raw)
            messages.append({
                "id":      msg_id,
                "from":    _decode_str(msg.get("From", "")),
                "to":      _decode_str(msg.get("To", "")),
                "subject": _decode_str(msg.get("Subject", "(no subject)")),
                "date":    _decode_str(msg.get("Date", "")),
                "body":    _get_body(msg),
            })
        except Exception as e:
            print(f"  [warn] Could not fetch message {msg_id}: {e}")
    return messages


def _classify_status(sent: list[dict], received: list[dict]) -> str:
    """Determine application status from sent and received threads."""
    if not sent and not received:
        return "NO_CONTACT"

    body_all = " ".join(
        (m["subject"] + " " + m["body"]).lower() for m in received
    )

    # Positive confirmations
    confirm_keywords = [
        "confirmation", "confirmé", "confirmée", "reçu", "received",
        "enregistré", "registered", "dossier complet", "pris en compte",
        "accusé de réception", "acknowledged", "convocation",
        "rendez-vous", "appointment", "récépissé",
    ]
    # Rejection / problem keywords
    reject_keywords = [
        "rejeté", "rejected", "refusé", "refusal", "refused",
        "incomplet", "incomplete", "manquant", "missing",
        "ne peut pas", "cannot", "annulé", "cancelled",
    ]

    has_confirm = any(kw in body_all for kw in confirm_keywords)
    has_reject  = any(kw in body_all for kw in reject_keywords)

    if has_reject:
        return "ISSUE_FOUND"
    if has_confirm:
        return "CONFIRMED"
    if received:
        return "REPLIED"   # got a reply but no clear keyword
    if sent:
        return "SENT_AWAITING_REPLY"
    return "NO_CONTACT"


STATUS_LABELS = {
    "CONFIRMED":            ("✔  APPLICATION CONFIRMED",     "\033[92m"),
    "REPLIED":              ("↩  REPLY RECEIVED (unclassified)", "\033[93m"),
    "ISSUE_FOUND":          ("✖  ISSUE / PROBLEM DETECTED",  "\033[91m"),
    "SENT_AWAITING_REPLY":  ("⏳  EMAIL SENT — AWAITING REPLY", "\033[94m"),
    "NO_CONTACT":           ("○  NO EMAILS FOUND WITH THIS ADDRESS", "\033[90m"),
}

RESET = "\033[0m"


def _print_message(m: dict, direction: str):
    print(f"\n  {'─'*56}")
    print(f"  [{direction}]")
    print(f"  Date   : {m['date']}")
    print(f"  From   : {m['from']}")
    print(f"  To     : {m['to']}")
    print(f"  Subject: {m['subject']}")
    body_preview = m["body"][:400].replace("\n", " ").strip()
    if body_preview:
        print(f"  Body   : {body_preview}{'...' if len(m['body']) > 400 else ''}")


def run(target: str = DEFAULT_TARGET):
    print(f"\n{'='*60}")
    print(f"  Gmail Application Tracker")
    print(f"  Account : {GMAIL_USER}")
    print(f"  Target  : {target}")
    print(f"  Time    : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    print("\n[1] Connecting to Gmail IMAP...")
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        imap.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        print("  Connected.")
    except imaplib.IMAP4.error as e:
        print(f"\n[ERROR] Login failed: {e}")
        print("  Make sure GMAIL_APP_PASSWORD is set in .env or the env variable.")
        sys.exit(1)

    target_safe = re.escape(target)

    # ── Search INBOX for emails FROM the target ────────────────────────────────
    print(f"\n[2] Searching INBOX for emails FROM {target}...")
    inbox_ids = _search_folder(imap, "INBOX", f'(FROM "{target}")')
    inbox_msgs = _fetch_messages(imap, inbox_ids)
    print(f"  Found: {len(inbox_msgs)} message(s)")

    # ── Search Sent for emails TO the target ──────────────────────────────────
    print(f"\n[3] Searching Sent for emails TO {target}...")
    sent_ids = _search_folder(imap, '"[Gmail]/Sent Mail"', f'(TO "{target}")')
    sent_msgs = _fetch_messages(imap, sent_ids)
    print(f"  Found: {len(sent_msgs)} message(s)")

    # Also try All Mail for any stray threads
    print(f"\n[4] Searching All Mail for any thread with {target}...")
    all_ids_from = _search_folder(imap, '"[Gmail]/All Mail"', f'(FROM "{target}")')
    all_ids_to   = _search_folder(imap, '"[Gmail]/All Mail"', f'(TO "{target}")')
    all_ids = list(set(all_ids_from + all_ids_to) - set(inbox_ids) - set(sent_ids))
    all_msgs = _fetch_messages(imap, all_ids)
    print(f"  Found: {len(all_msgs)} additional message(s)")

    imap.logout()

    # ── Classify ───────────────────────────────────────────────────────────────
    received_all = inbox_msgs + [m for m in all_msgs if target.lower() in m["from"].lower()]
    sent_all     = sent_msgs  + [m for m in all_msgs if target.lower() in m["to"].lower()]

    status = _classify_status(sent_all, received_all)
    label, color = STATUS_LABELS[status]

    print(f"\n{'='*60}")
    print(f"  STATUS: {color}{label}{RESET}")
    print(f"{'='*60}")

    # ── Print threads ──────────────────────────────────────────────────────────
    if sent_all:
        print(f"\n  YOUR SENT EMAILS ({len(sent_all)}):")
        for m in sorted(sent_all, key=lambda x: x["date"]):
            _print_message(m, "SENT")

    if received_all:
        print(f"\n  RECEIVED EMAILS ({len(received_all)}):")
        for m in sorted(received_all, key=lambda x: x["date"]):
            _print_message(m, "RECEIVED")

    if not sent_all and not received_all:
        print(f"\n  No emails found involving {target}.")
        print("  Double-check the address or that the email was sent from this account.")

    # ── Advice ────────────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    if status == "CONFIRMED":
        print("  Your application appears to have been RECEIVED and CONFIRMED.")
        print("  Check any convocation or récépissé details above.")
    elif status == "ISSUE_FOUND":
        print("  A PROBLEM was detected in the reply. Review the email body above.")
        print("  You may need to resubmit documents or contact the office.")
    elif status == "SENT_AWAITING_REPLY":
        print("  You sent an email but have NOT received a reply yet.")
        print("  Consider following up if it has been more than 5 business days.")
    elif status == "REPLIED":
        print("  A reply was received — review the content above to confirm status.")
    else:
        print(f"  No correspondence found with {target}.")
        print("  If you applied via a web form, check for a confirmation email")
        print("  from a different address (e.g. noreply@val-doise.gouv.fr).")
    print()

    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track Gmail correspondence with a target address.")
    parser.add_argument(
        "--sender",
        default=DEFAULT_TARGET,
        help=f"Email address to search for (default: {DEFAULT_TARGET})",
    )
    args = parser.parse_args()
    run(target=args.sender)
