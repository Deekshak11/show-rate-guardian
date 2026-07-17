from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("showrate")


CONFIG_DIR = Path(__file__).resolve().parent.parent / "references"
PROFILE_PATH = CONFIG_DIR / "profile.yaml"


def load_config() -> dict:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "showrate-guardian-factory" / "scripts"))
    from showrate_lib import load_profile
    return load_profile(PROFILE_PATH)


def env(name: str, required: bool = True) -> str:
    value = os.environ.get(name, "")
    if required and not value:
        raise EnvironmentError(f"Missing required env var: {name}")
    return value


def parse_dt(dt_str: str) -> datetime:
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {dt_str}")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def hours_until(event_time: str) -> float:
    try:
        target = parse_dt(event_time)
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        diff = target - now_utc()
        return max(0, diff.total_seconds() / 3600)
    except Exception:
        return 0


class GHLClient:
    BASE = "https://services.leadconnectorhq.com"

    def __init__(self, lazy: bool = False, dry_run: bool = False):
        self._dry_run = dry_run or not os.environ.get("SHOWRATE_CRM_TOKEN")
        self._token = "" if (lazy or self._dry_run) else env("SHOWRATE_CRM_TOKEN")
        self._headers = None

    @property
    def headers(self):
        if self._headers is None:
            if not self._token:
                self._token = env("SHOWRATE_CRM_TOKEN")
            self._headers = {
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "Version": "2021-07-28",
            }
        return self._headers

    def get_contact(self, contact_id: str) -> dict | None:
        if self._dry_run:
            logger.info("[DRY RUN] GHL get_contact: %s", contact_id)
            return {"id": contact_id, "tags": ["showrate-booked"], "firstName": "Test"}
        r = httpx.get(f"{self.BASE}/contacts/{contact_id}", headers=self.headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("contact", {})
        logger.warning("GHL get_contact %s: %s", contact_id, r.status_code)
        return None

    def update_contact(self, contact_id: str, data: dict) -> bool:
        if self._dry_run:
            logger.info("[DRY RUN] GHL update_contact %s: %s", contact_id, json.dumps(data)[:200])
            return True
        r = httpx.put(f"{self.BASE}/contacts/{contact_id}", headers=self.headers, json=data, timeout=15)
        if r.status_code in (200, 201):
            return True
        logger.warning("GHL update_contact %s: %s %s", contact_id, r.status_code, r.text[:200])
        return False

    def add_note(self, contact_id: str, body: str) -> bool:
        if self._dry_run:
            logger.info("[DRY RUN] GHL add_note %s: %s", contact_id, body[:100])
            return True
        r = httpx.post(
            f"{self.BASE}/contacts/{contact_id}/notes",
            headers=self.headers,
            json={"body": body},
            timeout=15,
        )
        return r.status_code in (200, 201)

    def add_tag(self, contact_id: str, tag: str) -> bool:
        contact = self.get_contact(contact_id)
        if not contact:
            return False
        tags = contact.get("tags", [])
        if tag in tags:
            return True
        tags.append(tag)
        return self.update_contact(contact_id, {"tags": tags})

    def remove_tag(self, contact_id: str, tag: str) -> bool:
        contact = self.get_contact(contact_id)
        if not contact:
            return False
        tags = [t for t in contact.get("tags", []) if t != tag]
        return self.update_contact(contact_id, {"tags": tags})


class CalendlyClient:
    BASE = "https://api.calendly.com"

    def __init__(self, lazy: bool = False, dry_run: bool = False):
        self._dry_run = dry_run or not os.environ.get("SHOWRATE_SCHEDULER_TOKEN")
        self._token = "" if (lazy or self._dry_run) else env("SHOWRATE_SCHEDULER_TOKEN")
        self._headers = None

    @property
    def headers(self):
        if self._headers is None:
            if not self._token:
                self._token = env("SHOWRATE_SCHEDULER_TOKEN")
            self._headers = {
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            }
        return self._headers

    def get_event(self, uri: str) -> dict | None:
        if self._dry_run:
            logger.info("[DRY RUN] Calendly get_event: %s", uri)
            return {"uri": uri, "status": "active"}
        r = httpx.get(uri, headers=self.headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("resource", {})
        logger.warning("Calendly get_event %s: %s", uri, r.status_code)
        return None

    def cancel_event(self, uri: str, reason: str = "") -> bool:
        if self._dry_run:
            logger.info("[DRY RUN] Calendly cancel_event: %s (%s)", uri, reason)
            return True
        r = httpx.post(
            f"{uri}/cancellation",
            headers=self.headers,
            json={"reason": reason or "Cancelled by ShowRate Guardian"},
            timeout=15,
        )
        return r.status_code in (200, 201)

    def get_user(self) -> dict | None:
        r = httpx.get(f"{self.BASE}/users/me", headers=self.headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("resource", {})
        return None

    def list_event_types(self, user_uri: str) -> list[dict]:
        r = httpx.get(
            f"{self.BASE}/event_types",
            headers=self.headers,
            params={"user": user_uri},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("collection", [])
        return []

    def webhook_subscribe(self, callback_url: str, events: list[str], user_uri: str, scope: str = "user") -> dict | None:
        r = httpx.post(
            f"{self.BASE}/webhook_subscriptions",
            headers=self.headers,
            json={
                "url": callback_url,
                "events": events,
                "organization": "",
                "user": user_uri,
                "scope": scope,
            },
            timeout=15,
        )
        if r.status_code in (200, 201):
            return r.json().get("subscription", {})
        logger.warning("Calendly webhook subscribe: %s %s", r.status_code, r.text[:200])
        return None


class TwilioClient:
    BASE = "https://api.twilio.com/2010-04-01"

    def __init__(self, lazy: bool = False, dry_run: bool = False):
        self._dry_run = dry_run or not os.environ.get("SHOWRATE_SMS_TOKEN")
        self._lazy = lazy
        self.account_sid = "" if (lazy or self._dry_run) else (env("SHOWRATE_TWILIO_SID", required=False) or env("SHOWRATE_SMS_TOKEN"))
        self.auth_token = "" if (lazy or self._dry_run) else env("SHOWRATE_TWILIO_AUTH_TOKEN", required=False)
        self.from_number = "" if (lazy or self._dry_run) else env("SHOWRATE_TWILIO_FROM_NUMBER", required=False)
        self._client = None

    def _ensure_creds(self):
        if not self.account_sid:
            self.account_sid = env("SHOWRATE_TWILIO_SID", required=False) or env("SHOWRATE_SMS_TOKEN")
        if not self.auth_token:
            self.auth_token = env("SHOWRATE_TWILIO_AUTH_TOKEN", required=False)
        if not self.from_number:
            self.from_number = env("SHOWRATE_TWILIO_FROM_NUMBER", required=False)

    @property
    def client(self):
        if self._client is None:
            self._ensure_creds()
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                self._client = "httpx"
        return self._client

    def send_sms(self, to: str, body: str) -> dict | None:
        if self._dry_run:
            logger.info("[DRY RUN] Twilio SMS to %s: %s", to, body[:100])
            return {"status": "dry_run", "to": to, "body": body[:80]}
        if self.client == "httpx":
            return self._send_sms_httpx(to, body)
        try:
            msg = self.client.messages.create(to=to, from_=self.from_number, body=body)
            return {"sid": msg.sid, "status": msg.status}
        except Exception as exc:
            logger.error("Twilio SMS failed: %s", exc)
            return None

    def _send_sms_httpx(self, to: str, body: str) -> dict | None:
        url = f"{self.BASE}/Accounts/{self.account_sid}/Messages.json"
        r = httpx.post(
            url,
            auth=(self.account_sid, self.auth_token),
            data={"To": to, "From": self.from_number, "Body": body},
            timeout=15,
        )
        if r.status_code in (200, 201):
            return r.json()
        logger.error("Twilio SMS httpx failed: %s %s", r.status_code, r.text[:200])
        return None


def verify_calendly_signature(payload: bytes, signature_header: str, webhook_key: str) -> bool:
    if not signature_header or not webhook_key:
        return False
    parts = dict(p.split("=") for p in signature_header.split(",") if "=" in p)
    t = parts.get("t", "")
    v1 = parts.get("v1", "")
    if not t or not v1:
        return False
    data = f"{t}.{payload.decode('utf-8', errors='replace')}"
    expected = hmac.new(webhook_key.encode(), data.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)
