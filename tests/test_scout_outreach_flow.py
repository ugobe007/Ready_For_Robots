import base64
import hashlib
import hmac
import json

from app.api.crm import _reply_address
from app.api.webhooks import _extract_addresses, _token_from_addresses, _verify_resend_signature


def test_reply_address_uses_plus_token(monkeypatch):
    monkeypatch.setenv("SCOUT_REPLY_DOMAIN", "reply.readyforrobots.com")

    assert _reply_address("abc123") == "reply+abc123@reply.readyforrobots.com"


def test_inbound_reply_token_extracted_from_address():
    addresses = _extract_addresses(["SCOUT <reply+thread_token@readyforrobots.com>"])

    assert addresses == ["reply+thread_token@readyforrobots.com"]
    assert _token_from_addresses(addresses) == "thread_token"


def test_resend_signature_verification_accepts_svix_signature(monkeypatch):
    raw_secret = b"secret bytes"
    monkeypatch.setenv("RESEND_WEBHOOK_SECRET", f"whsec_{base64.b64encode(raw_secret).decode()}")
    payload = json.dumps({"type": "email.received"}).encode()
    svix_id = "msg_test"
    svix_timestamp = "1715630000"
    signed = f"{svix_id}.{svix_timestamp}.".encode() + payload
    signature = base64.b64encode(hmac.new(raw_secret, signed, hashlib.sha256).digest()).decode()

    _verify_resend_signature(payload, svix_id, svix_timestamp, f"v1,{signature}")
