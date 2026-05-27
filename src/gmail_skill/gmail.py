"""Gmail API: send, reply, reply_all, archive."""
import base64
import email.mime.multipart
import email.mime.text

from .auth import get_gmail_service
from .storage import init_db, save_message_meta, save_eml, save_markdown


# ── Send ──────────────────────────────────────────────────────────────────────

def _build_raw(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    in_reply_to: str = "",
    references: str = "",
    thread_id: str = "",
) -> dict:
    msg = email.mime.multipart.MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = f"{references} {in_reply_to}".strip()

    msg.attach(email.mime.text.MIMEText(body, "plain", "utf-8"))

    payload = {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}
    if thread_id:
        payload["threadId"] = thread_id
    return payload


def send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> dict:
    service = get_gmail_service()
    sent = service.users().messages().send(
        userId="me", body=_build_raw(to=to, subject=subject, body=body, cc=cc, bcc=bcc)
    ).execute()
    return {"id": sent["id"], "thread_id": sent["threadId"], "status": "sent"}


def reply_email(thread_id: str, body: str, reply_all: bool = False) -> dict:
    service = get_gmail_service()

    thread = service.users().threads().get(
        userId="me", id=thread_id, format="metadata"
    ).execute()
    messages = thread.get("messages", [])
    if not messages:
        raise ValueError(f"Thread {thread_id} has no messages")

    last = messages[-1]
    hdrs = {h["name"].lower(): h["value"] for h in last.get("payload", {}).get("headers", [])}

    to = hdrs.get("from", "")
    subject = hdrs.get("subject", "")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    message_id = hdrs.get("message-id", "")
    references = hdrs.get("references", "")

    cc = ""
    if reply_all:
        seen = {to}
        parts = []
        for field in ("to", "cc"):
            for addr in hdrs.get(field, "").split(","):
                addr = addr.strip()
                if addr and addr not in seen:
                    seen.add(addr)
                    parts.append(addr)
        cc = ", ".join(parts)

    sent = service.users().messages().send(
        userId="me",
        body=_build_raw(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            in_reply_to=message_id,
            references=references,
            thread_id=thread_id,
        ),
    ).execute()
    return {"id": sent["id"], "thread_id": sent["threadId"], "status": "sent"}


# ── Archive ───────────────────────────────────────────────────────────────────

def _extract_text(payload: dict) -> str:
    """Recursively pull text/plain from a MIME payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        text = _extract_text(part)
        if text:
            return text
    return ""


def archive_message(msg_id: str) -> dict:
    init_db()
    service = get_gmail_service()

    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    save_message_meta(msg)

    raw_msg = service.users().messages().get(userId="me", id=msg_id, format="raw").execute()
    save_eml(msg_id, base64.urlsafe_b64decode(raw_msg["raw"]))

    hdrs = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    body = _extract_text(msg.get("payload", {}))
    md_path = save_markdown(
        msg_id,
        subject=hdrs.get("subject", ""),
        sender=hdrs.get("from", ""),
        date=hdrs.get("date", ""),
        body=body,
    )
    return {"id": msg_id, "subject": hdrs.get("subject", ""), "md_path": str(md_path)}


def archive_sync(days_back: int = 7, max_messages: int = 200) -> dict:
    from datetime import datetime, timedelta

    init_db()
    service = get_gmail_service()

    after = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    results = service.users().messages().list(
        userId="me", q=f"after:{after}", maxResults=max_messages
    ).execute()

    archived, errors = 0, 0
    for ref in results.get("messages", []):
        try:
            archive_message(ref["id"])
            archived += 1
        except Exception:
            errors += 1

    return {"synced": archived, "errors": errors, "days_back": days_back}
