"""Pravesh Setu Medical link for applications opened from the Pravesh Setu app.

The app opens the form with a single-use launch token in the URL fragment.
The form sends it with the submission; we keep only its SHA-256 hash.
After a successful submission we send Pravesh Setu a signed event carrying
the reference, the token hash and the official filled-form PDF. Pravesh Setu
verifies the Ed25519 signature with our public key, checks the token belongs
to a verified student, and files the PDF in that student's My Documents.

Environment:
  PS_SIGNING_KEY   base64 Ed25519 private key seed (32 bytes). Unset = link disabled.
  PS_EVENT_URL     Pravesh Setu event endpoint
                   (default https://ifd-api.onrender.com/api/integrations/neet-form/events)
"""
import base64
import hashlib
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

log = logging.getLogger("pravesh_setu")

EVENT_URL = os.getenv("PS_EVENT_URL", "https://ifd-api.onrender.com/api/integrations/neet-form/events")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
RESEND_COOLDOWN = timedelta(seconds=15)


def _signing_key():
    seed = os.getenv("PS_SIGNING_KEY", "").strip()
    if not seed:
        return None
    raw = base64.b64decode(seed)
    if len(raw) != 32:
        raise RuntimeError("PS_SIGNING_KEY must be a base64 32-byte Ed25519 seed.")
    return Ed25519PrivateKey.from_private_bytes(raw)


def enabled() -> bool:
    return _signing_key() is not None


def hash_launch_token(token: str) -> str:
    """'' unless the token has the exact format Pravesh Setu issues."""
    token = (token or "").strip()
    if not TOKEN_RE.match(token):
        return ""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def sign(body: bytes, timestamp: str) -> str:
    key = _signing_key()
    if key is None:
        raise RuntimeError("PS_SIGNING_KEY is not configured.")
    return base64.b64encode(key.sign(timestamp.encode() + b"." + body)).decode()


def _post(body: bytes, timeout: float):
    timestamp = str(int(time.time()))
    request = urllib.request.Request(EVENT_URL, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "X-BFEG-Timestamp": timestamp,
        "X-BFEG-Signature": sign(body, timestamp),
        "User-Agent": "bfeg-portal/1.0",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as err:
        try:
            payload = json.loads(err.read() or b"{}")
        except ValueError:
            payload = {}
        return err.code, payload


def push_submission(sub, db, event_type="submission.created", attempts=2, timeout=25.0):
    """Send the signed event for one submission and record the outcome on it.

    Returns {"linked": bool, "message": str}. Never raises: the student's
    application is already saved whatever happens here.
    """
    if not sub.ps_launch_hash:
        return {"linked": False, "message": "Not opened from Pravesh Setu."}
    if not enabled():
        sub.ps_sync_status, sub.ps_sync_error = "not_configured", "PS_SIGNING_KEY is not set."
        db.commit()
        return {"linked": False, "message": "Pravesh Setu link is not configured."}

    pdf_b64, pdf_error = None, None
    try:
        from .pdf_form import build_form_pdf
        pdf_b64 = base64.b64encode(build_form_pdf(sub)).decode()
    except Exception as exc:  # The submission still links; Pravesh Setu can ask again later.
        log.exception("Form PDF generation failed for %s", sub.reference)
        pdf_error = f"Form PDF generation failed: {type(exc).__name__}"

    submitted = sub.created_at or datetime.now(timezone.utc)
    if submitted.tzinfo is None:
        submitted = submitted.replace(tzinfo=timezone.utc)
    body = json.dumps({
        "event_id": f"{sub.reference}:{uuid.uuid4().hex}",
        "type": event_type,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "reference": sub.reference,
        "launch_token_hash": sub.ps_launch_hash,
        "submitted_at": submitted.isoformat(),
        "applicant_name": sub.full_name or "",
        "pdf": {"base64": pdf_b64} if pdf_b64 else None,
        "pdf_error": pdf_error,
    }, separators=(",", ":")).encode()

    outcome = {"linked": False, "message": "Pravesh Setu could not be reached."}
    for attempt in range(attempts):
        try:
            status, payload = _post(body, timeout)
        except Exception as exc:  # network error / timeout
            outcome = {"linked": False, "message": f"Pravesh Setu could not be reached ({type(exc).__name__})."}
            time.sleep(1.5 * (attempt + 1))
            continue
        if 200 <= status < 300:
            outcome = {"linked": bool(payload.get("linked")), "message": str(payload.get("message") or "")[:300]}
            break
        outcome = {"linked": False, "message": str(payload.get("message") or f"HTTP {status}")[:300]}
        if status < 500:  # rejected (bad link, expired launch...) — retrying will not help
            break
        time.sleep(1.5 * (attempt + 1))

    sub.ps_sync_status = "linked" if outcome["linked"] else "failed"
    sub.ps_sync_error = "" if outcome["linked"] else outcome["message"]
    sub.ps_last_attempt_at = datetime.now(timezone.utc)
    db.commit()
    return outcome


def may_resend(sub) -> bool:
    last = sub.ps_last_attempt_at
    if last is None:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - last >= RESEND_COOLDOWN
